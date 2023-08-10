from database import models
from database.tests.factory import PipelineFactory, WorkflowFactory
from services.fetch_data import FetchDataService, UpdateFields
from services.fetch_data.datasources.circleci import CircleCIDataDriver


class TestFetchDataService(object):
    def test_sync_model(self, dbsession):
        pipeline = PipelineFactory()
        workflow_already_there = WorkflowFactory(
            status="success", pipeline=pipeline, external_id="already_there"
        )
        workflow_already_there_to_update = WorkflowFactory(
            status="created",
            pipeline=pipeline,
            external_id="already_there_needs_update",
        )
        dbsession.add_all(
            [pipeline, workflow_already_there, workflow_already_there_to_update]
        )
        dbsession.flush()
        raw_data = [
            {
                "pipeline": pipeline,
                "pipeline_id": "5034460f-c7c4-4c43-9457-de07e2029e7b",
                "canceled_by": "026a6d28-c22e-4aab-a8b4-bd7131a8ea35",
                "id": "already_there",
                "name": "build-and-test",
                "project_slug": "gh/CircleCI-Public/api-preview-docs",
                "errored_by": "c6e40f70-a80a-4ccc-af88-8d985a7bc622",
                "tag": "setup",
                "status": "success",
                "started_by": "03987f6a-4c27-4dc1-b6ab-c7e83bb3e713",
                "pipeline_number": "25",
                "created_at": "2019-08-24T14:15:22Z",
                "stopped_at": "2019-08-24T14:15:22Z",
            },
            {
                "pipeline": pipeline,
                "pipeline_id": "5034460f-c7c4-4c43-9457-de07e2029e7b",
                "canceled_by": "026a6d28-c22e-4aab-a8b4-bd7131a8ea35",
                "id": "already_there_needs_update",
                "name": "build-and-test",
                "project_slug": "gh/CircleCI-Public/api-preview-docs",
                "errored_by": "c6e40f70-a80a-4ccc-af88-8d985a7bc622",
                "tag": "setup",
                "status": "success",
                "started_by": "03987f6a-4c27-4dc1-b6ab-c7e83bb3e713",
                "pipeline_number": "25",
                "created_at": "2019-08-24T14:15:22Z",
                "stopped_at": "2019-08-24T14:15:22Z",
            },
            {
                "pipeline": pipeline,
                "pipeline_id": "5034460f-c7c4-4c43-9457-de07e2029e7b",
                "canceled_by": "026a6d28-c22e-4aab-a8b4-bd7131a8ea35",
                "id": "new_workflow",
                "name": "build-and-test",
                "project_slug": "gh/CircleCI-Public/api-preview-docs",
                "errored_by": "c6e40f70-a80a-4ccc-af88-8d985a7bc622",
                "tag": "setup",
                "status": "success",
                "started_by": "03987f6a-4c27-4dc1-b6ab-c7e83bb3e713",
                "pipeline_number": "25",
                "created_at": "2019-08-24T14:15:22Z",
                "stopped_at": "2019-08-24T14:15:22Z",
            },
        ]

        # TODO: create a fake data provider
        data_driver = CircleCIDataDriver()
        fetch_data_service = FetchDataService(dbsession, {})
        models_synced = fetch_data_service._sync_model(
            raw_data=raw_data,
            model=models.Workflow,
            datadriver=data_driver,
            update_fields=[UpdateFields("status", "status")],
        )
        assert len(models_synced) == 2
        assert workflow_already_there_to_update in models_synced
