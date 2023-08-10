import asyncio
from collections import namedtuple
from typing import List

from database.models import Job, Pipeline, Project, Workflow
from services.fetch_data.datasources import BaseDatasource, get_datasource_class
from services.fetch_data.datasources.error import DatasourceNotFoundError
from utils.logging_config import LOGGER_NAME

UpdateFields = namedtuple("UpdateField", ["model_field", "raw_data_field"])

import logging

logger = logging.getLogger(LOGGER_NAME)


class FetchDataService(object):
    def __init__(self, dbsession, config: dict = None) -> None:
        if config is None:
            config = {}
        self.config = config
        self.dbsession = dbsession

    def _sync_model(
        self, raw_data: List[dict], model, datadriver, update_fields: List[UpdateFields]
    ):
        all_ids = set(map(lambda item: item["id"], raw_data))
        ids_in_db = set(
            item[0]
            for item in self.dbsession.query(model.external_id)
            .filter(model.external_id.in_(all_ids))
            .all()  # returns tuples
        )
        # Instert models we don't yet have
        ids_to_insert = all_ids - ids_in_db
        raw_data_to_insert = filter(lambda item: item["id"] in ids_to_insert, raw_data)
        objects_to_insert = list(
            map(
                lambda item: datadriver.to_db_representation(item, model),
                raw_data_to_insert,
            )
        )
        self.dbsession.add_all(objects_to_insert)
        # Update models we do have
        models_to_update = sorted(
            self.dbsession.query(model).filter(model.external_id.in_(ids_in_db)).all(),
            key=lambda item: item.external_id,
        )
        raw_data_to_update = sorted(
            filter(lambda item: item["id"] in ids_in_db, raw_data),
            key=lambda item: item["id"],
        )
        data_pack = zip(models_to_update, raw_data_to_update)
        updated_objects = []
        for pair in data_pack:
            instance, raw_data = pair
            updated = False
            for field in update_fields:
                # We need to annotate what models actually changed
                if (
                    getattr(instance, field.model_field)
                    != raw_data[field.raw_data_field]
                ):
                    updated = True
                    setattr(instance, field.model_field, raw_data[field.raw_data_field])
            if updated:
                updated_objects.append(instance)
        return objects_to_insert + updated_objects

    async def sync_pipelines(self, project: Project, datasource):
        all_synced_pipelines = []
        fields_to_update = [UpdateFields("status", "state")]
        async for pipelines in datasource.get_all_project_pipelines(project):
            synced_pipelines = self._sync_model(
                pipelines, Pipeline, datasource.data_driver, fields_to_update
            )
            self.dbsession.flush()
            all_synced_pipelines.extend(synced_pipelines)
        logger.info(
            f"Synced all pipelines",
            extra=dict(
                extra_log_attributes=dict(
                    project=project.id, pipeline_count=len(all_synced_pipelines)
                )
            ),
        )
        return all_synced_pipelines

    async def sync_workflows(self, pipeline: Pipeline, datasource):
        all_synced_workflows = []
        fields_to_update = [
            UpdateFields("status", "status"),
            UpdateFields("stopped_at", "stopped_at"),
        ]
        async for workflows in datasource.get_pipeline_workflows(pipeline):
            synced_workflows = self._sync_model(
                workflows, Workflow, datasource.data_driver, fields_to_update
            )
            self.dbsession.flush()
            all_synced_workflows.extend(synced_workflows)
        logger.info(
            f"Synced all workflows",
            extra=dict(
                extra_log_attributes=dict(
                    pipeline=pipeline.id, workflow_count=len(all_synced_workflows)
                )
            ),
        )
        return all_synced_workflows

    async def sync_jobs(self, workflow: Workflow, datasource):
        all_synced_jobs = []
        fields_to_update = [
            UpdateFields("status", "status"),
            UpdateFields("stopped_at", "stopped_at"),
        ]
        async for jobs_data in datasource.get_workflow_jobs(workflow):
            # We don't need to save all jobs, only the ones that interest us
            standarized_data = list(
                map(
                    lambda item: datasource.data_driver.to_db_representation(item, Job),
                    jobs_data,
                )
            )
            pairs = zip(jobs_data, standarized_data)
            jobs_of_interest = []
            for raw_data, parsed_data in pairs:
                if parsed_data.name in [
                    workflow.label_analysis_job_name,
                    workflow.regular_tests_job_name,
                ]:
                    jobs_of_interest.append(raw_data)

            synced_jobs = self._sync_model(
                jobs_of_interest, Job, datasource.data_driver, fields_to_update
            )
            self.dbsession.flush()
            all_synced_jobs.extend(synced_jobs)
        logger.info(
            f"Synced all jobs",
            extra=dict(
                extra_log_attributes=dict(
                    workflow=workflow.id, job_count=len(all_synced_jobs)
                )
            ),
        )
        return synced_jobs

    async def sync_project(self, project: Project):
        datasource_class = get_datasource_class(project.ci_provider)
        if datasource_class is None:
            raise DatasourceNotFoundError(f"Missing DataSource {datasource_class}")
        datasource: BaseDatasource = datasource_class(self.config)

        # Sync pipelines
        synced_pipelines = await self.sync_pipelines(
            project=project, datasource=datasource
        )
        # Sync workflows
        all_synced_workflows = await asyncio.gather(
            *[
                asyncio.create_task(
                    self.sync_workflows(pipeline=pipeline, datasource=datasource)
                )
                for pipeline in synced_pipelines
            ]
        )
        for synced_workflows in all_synced_workflows:
            # For some reason this will return a list of lists
            # Sync Jobs
            await asyncio.gather(
                *[
                    asyncio.create_task(self.sync_jobs(workflow, datasource))
                    for workflow in synced_workflows
                ]
            )
