from datetime import datetime
from typing import Dict

import httpx

from config import get_config
from database.models import Job, Pipeline, Workflow
from database.models.project import Project
from services.fetch_data.datasources.base import BaseDatasource
from services.fetch_data.datasources.error import DatasourceConfigError


class CircleCIDatasource(BaseDatasource):
    """This class connects to the CircleCI API to retrieve data."""

    BASE_URL = "https://circleci.com/api/v2"

    @property
    def data_driver(self):
        return self._data_driver

    def __init__(self, config: Dict):
        self.api_token = get_config(config, "datasources", "circleci", "api_token")
        self._data_driver = CircleCIDataDriver()

        if self.api_token is None:
            raise DatasourceConfigError("Missing API TOKEN")

        super().__init__()

    # TODO: Create generator function that yields the pages when there are multiple pages

    async def _execute_request(
        self, method: str, url: str, headers: dict = None, params: dict = None
    ):
        if headers is None:
            headers = {}
        headers = {**headers, "Circle-Token": self.api_token}
        async with httpx.AsyncClient(base_url=self.BASE_URL) as client:
            response = await client.request(method, url, headers=headers, params=params)
            return response.json()
        # TODO: Handle errors and such

    async def get_all_project_pipelines(self, project: Project):
        # Get a list of all project's pipelines
        # https://circleci.com/docs/api/v2/index.html#operation/listPipelinesForProject
        # TODO: Handle the multiple pages
        url = f"/project/{self.data_driver.get_project_slug(project)}/pipeline"

        response = await self._execute_request("GET", url)
        # Extend raw data with `project` key
        items = response.get("items", [])
        extended_items = [{**item, "project": project} for item in items]
        return extended_items

    async def get_pipeline_workflows(self, pipeline: Pipeline):
        # Get pipeline's workflows
        # https://circleci.com/docs/api/v2/index.html#operation/listWorkflowsByPipelineId
        # TODO: Handle the multiple pages. Hopefully turning this into a generator function

        url = f"/pipeline/{pipeline.external_id}/workflow"

        response = await self._execute_request("GET", url)
        # Include the key `pipeline` in the data
        items = response.get("items", [])
        extended_items = [{**item, "pipeline": pipeline} for item in items]
        return extended_items

    async def get_workflow_jobs(self, workflow: Workflow):
        # Get a workflow's jobs
        # https://circleci.com/docs/api/v2/index.html#operation/listWorkflowJobs
        # TODO: Handle the multiple pages

        url = f"/workflow/{workflow.external_id}/job"

        response = await self._execute_request("GET", url)
        # Extend raw data with `workflow` key
        items = response.get("items", [])
        extended_items = [{**item, "workflow": workflow} for item in items]
        return extended_items


class CircleCIDataDriver(object):
    """This class translates CircleCI API data to internal representations"""

    def get_project_slug(self, project: Project) -> str:
        return (
            f"{project.git_provider.value}/{project.organization.name}/{project.name}"
        )

    def _to_job(self, circleci_data: dict) -> Job:
        job = Job(
            external_id=circleci_data["id"],
            workflow=circleci_data["workflow"],
            name=circleci_data["name"],
            number=circleci_data["job_number"],
            status=circleci_data["status"],
            started_at=datetime.fromisoformat(circleci_data["created_at"][:19]),
            stopped_at=datetime.fromisoformat(circleci_data["stopped_at"][:19]),
        )
        return job

    def _to_workflow(self, circleci_data: dict) -> Workflow:
        workflow = Workflow(
            external_id=circleci_data["id"],
            pipeline=circleci_data["pipeline"],
            name=circleci_data["name"],
            status=circleci_data["status"],
            started_at=datetime.fromisoformat(circleci_data["created_at"][:19]),
            stopped_at=datetime.fromisoformat(circleci_data["stopped_at"][:19]),
        )
        return workflow

    def _to_pipeline(self, circleci_data: dict) -> Pipeline:
        pipeline = Pipeline(
            project=circleci_data["project"],
            external_id=circleci_data["id"],
            number=circleci_data["number"],
            created_at=datetime.fromisoformat(circleci_data["created_at"][:19]),
            status=circleci_data["state"],
        )
        return pipeline

    def to_db_representation(self, circleci_data: dict, model_class):
        if issubclass(model_class, Pipeline):
            return self._to_pipeline(circleci_data)
        if issubclass(model_class, Workflow):
            return self._to_workflow(circleci_data)
        if issubclass(model_class, Job):
            return self._to_job(circleci_data)
        raise Exception(f"Unknown model {model_class}")
