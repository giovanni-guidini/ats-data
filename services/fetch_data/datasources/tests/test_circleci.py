import unittest
from copy import deepcopy
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

from database.models.job import Job
from database.models.pipeline import Pipeline
from database.models.workflow import Workflow
from database.tests.factory import PipelineFactory, ProjectFactory, WorkflowFactory
from services.fetch_data.datasources.circleci import (
    CircleCIDataDriver,
    CircleCIDatasource,
)
from services.fetch_data.datasources.error import DatasourceConfigError


class TestCircleCIDatasource(object):
    config = {"datasources": {"circleci": {"api_token": "your_api_token_here"}}}

    def test_missing_api_token(self):
        # Remove the API token from the config
        config = deepcopy(self.config)
        config["datasources"]["circleci"]["api_token"] = None

        with pytest.raises(DatasourceConfigError):
            CircleCIDatasource(config)

    @pytest.mark.asyncio
    @patch("services.fetch_data.datasources.circleci.httpx.AsyncClient")
    async def test_get_all_project_pipelines(self, mock_httpx_client, dbsession):
        project = ProjectFactory(
            organization__name="CircleCI-Public", name="api-preview-docs"
        )
        dbsession.add(project)
        example_response = {
            "items": [
                {
                    "id": "some-uuid4-id",
                    "errors": [],
                    "project_slug": "gh/CircleCI-Public/api-preview-docs",
                    "updated_at": "2019-08-24T14:15:22Z",
                    "number": "25",
                    "trigger_parameters": {},
                    "state": "created",
                    "created_at": "2019-08-24T14:15:22Z",
                    "trigger": {},
                    "vcs": {},
                }
            ],
            "next_page_token": "string",
        }

        mock_response = MagicMock(name="mock_response")
        mock_response.json.return_value = example_response
        mock_httpx_client.return_value.__aenter__.return_value.request.return_value = (
            mock_response
        )

        datasource = CircleCIDatasource(self.config)
        result = await datasource.get_all_project_pipelines(project)

        expected_result = [
            {
                "id": "some-uuid4-id",
                "errors": [],
                "project_slug": "gh/CircleCI-Public/api-preview-docs",
                "updated_at": "2019-08-24T14:15:22Z",
                "number": "25",
                "trigger_parameters": {},
                "state": "created",
                "created_at": "2019-08-24T14:15:22Z",
                "trigger": {},
                "vcs": {},
                "project": project,
            }
        ]
        assert result == expected_result

        mock_httpx_client.return_value.__aenter__.return_value.request.assert_called_once_with(
            "GET",
            f"/project/gh/CircleCI-Public/api-preview-docs/pipeline",
            headers={"Circle-Token": "your_api_token_here"},
            params=None,
        )

    @pytest.mark.asyncio
    @patch("services.fetch_data.datasources.circleci.httpx.AsyncClient")
    async def test_get_pipeline_workflows(self, mock_httpx_client, dbsession):
        pipeline = PipelineFactory()
        dbsession.add(pipeline)
        example_response = {
            "items": [
                {
                    "pipeline_id": "5034460f-c7c4-4c43-9457-de07e2029e7b",
                    "canceled_by": "026a6d28-c22e-4aab-a8b4-bd7131a8ea35",
                    "id": "497f6eca-6276-4993-bfeb-53cbbbba6f08",
                    "name": "build-and-test",
                    "project_slug": "gh/CircleCI-Public/api-preview-docs",
                    "errored_by": "c6e40f70-a80a-4ccc-af88-8d985a7bc622",
                    "tag": "setup",
                    "status": "success",
                    "started_by": "03987f6a-4c27-4dc1-b6ab-c7e83bb3e713",
                    "pipeline_number": "25",
                    "created_at": "2019-08-24T14:15:22Z",
                    "stopped_at": "2019-08-24T14:15:22Z",
                }
            ],
            "next_page_token": "string",
        }

        mock_response = MagicMock()
        mock_response.json.return_value = example_response
        mock_httpx_client.return_value.__aenter__.return_value.request.return_value = (
            mock_response
        )

        datasource = CircleCIDatasource(self.config)
        result = await datasource.get_pipeline_workflows(pipeline)

        expected_response = [
            {
                "pipeline": pipeline,
                "pipeline_id": "5034460f-c7c4-4c43-9457-de07e2029e7b",
                "canceled_by": "026a6d28-c22e-4aab-a8b4-bd7131a8ea35",
                "id": "497f6eca-6276-4993-bfeb-53cbbbba6f08",
                "name": "build-and-test",
                "project_slug": "gh/CircleCI-Public/api-preview-docs",
                "errored_by": "c6e40f70-a80a-4ccc-af88-8d985a7bc622",
                "tag": "setup",
                "status": "success",
                "started_by": "03987f6a-4c27-4dc1-b6ab-c7e83bb3e713",
                "pipeline_number": "25",
                "created_at": "2019-08-24T14:15:22Z",
                "stopped_at": "2019-08-24T14:15:22Z",
            }
        ]
        assert result == expected_response

        mock_httpx_client.return_value.__aenter__.return_value.request.assert_called_once_with(
            "GET",
            f"/pipeline/{pipeline.external_id}/workflow",
            headers={"Circle-Token": "your_api_token_here"},
            params=None,
        )

    @pytest.mark.asyncio
    @patch("services.fetch_data.datasources.circleci.httpx.AsyncClient")
    async def test_get_workflow_jobs(self, mock_httpx_client, dbsession):
        workflow = WorkflowFactory()
        dbsession.add(workflow)
        example_response = {
            "items": [
                {
                    "canceled_by": "026a6d28-c22e-4aab-a8b4-bd7131a8ea35",
                    "dependencies": [],
                    "job_number": 0,
                    "id": "497f6eca-6276-4993-bfeb-53cbbbba6f08",
                    "started_at": "2019-08-24T14:15:22Z",
                    "name": "string",
                    "approved_by": "02030314-b162-4b4d-8af1-88eabdcc615d",
                    "project_slug": "gh/CircleCI-Public/api-preview-docs",
                    "status": "success",
                    "type": "build",
                    "stopped_at": "2019-08-24T14:15:22Z",
                    "approval_request_id": "47bbf9d9-0b01-4281-9b67-9324ae3d0dff",
                }
            ],
            "next_page_token": "string",
        }

        mock_response = MagicMock()
        mock_response.json.return_value = example_response
        mock_httpx_client.return_value.__aenter__.return_value.request.return_value = (
            mock_response
        )

        datasource = CircleCIDatasource(self.config)
        result = await datasource.get_workflow_jobs(workflow)

        expected_response = [
            {
                "workflow": workflow,
                "canceled_by": "026a6d28-c22e-4aab-a8b4-bd7131a8ea35",
                "dependencies": [],
                "job_number": 0,
                "id": "497f6eca-6276-4993-bfeb-53cbbbba6f08",
                "started_at": "2019-08-24T14:15:22Z",
                "name": "string",
                "approved_by": "02030314-b162-4b4d-8af1-88eabdcc615d",
                "project_slug": "gh/CircleCI-Public/api-preview-docs",
                "status": "success",
                "type": "build",
                "stopped_at": "2019-08-24T14:15:22Z",
                "approval_request_id": "47bbf9d9-0b01-4281-9b67-9324ae3d0dff",
            }
        ]
        assert result == expected_response

        mock_httpx_client.return_value.__aenter__.return_value.request.assert_called_once_with(
            "GET",
            f"/workflow/{workflow.external_id}/job",
            headers={"Circle-Token": "your_api_token_here"},
            params=None,
        )


class TestCircleCIDataDriver(object):
    def test_to_pipeline(self, dbsession):
        project = ProjectFactory()
        dbsession.add(project)
        data_driver = CircleCIDataDriver()
        raw_pipeline_data = {
            "project": project,
            "id": "some-uuid4-id",
            "errors": [],
            "project_slug": "gh/CircleCI-Public/api-preview-docs",
            "updated_at": "2019-08-24T14:15:22Z",
            "number": "25",
            "trigger_parameters": {},
            "state": "created",
            "created_at": "2019-08-24T14:15:22Z",
            "trigger": {},
            "vcs": {},
        }
        pipeline = data_driver._to_pipeline(raw_pipeline_data)
        assert isinstance(pipeline, Pipeline)
        assert pipeline.external_id == "some-uuid4-id"
        assert pipeline.status == "created"
        assert pipeline.number == "25"
        assert pipeline.project == project

    def test_to_workflow(self, dbsession):
        pipeline = PipelineFactory()
        dbsession.add(pipeline)
        data_driver = CircleCIDataDriver()
        raw_workflow_data = {
            "pipeline": pipeline,
            "pipeline_id": "5034460f-c7c4-4c43-9457-de07e2029e7b",
            "canceled_by": "026a6d28-c22e-4aab-a8b4-bd7131a8ea35",
            "id": "497f6eca-6276-4993-bfeb-53cbbbba6f08",
            "name": "build-and-test",
            "project_slug": "gh/CircleCI-Public/api-preview-docs",
            "errored_by": "c6e40f70-a80a-4ccc-af88-8d985a7bc622",
            "tag": "setup",
            "status": "success",
            "started_by": "03987f6a-4c27-4dc1-b6ab-c7e83bb3e713",
            "pipeline_number": "25",
            "created_at": "2019-08-24T14:15:22Z",
            "stopped_at": "2019-08-24T14:15:30Z",
        }
        workflow = data_driver._to_workflow(raw_workflow_data)
        assert isinstance(workflow, Workflow)
        assert workflow.external_id == "497f6eca-6276-4993-bfeb-53cbbbba6f08"
        assert workflow.status == "success"
        assert workflow.started_at == datetime(2019, 8, 24, 14, 15, 22)
        assert workflow.stopped_at == datetime(2019, 8, 24, 14, 15, 30)
        assert workflow.pipeline == pipeline

    def test_to_job(self, dbsession):
        workflow = WorkflowFactory()
        dbsession.add(workflow)
        data_driver = CircleCIDataDriver()
        raw_job_data = {
            "workflow": workflow,
            "canceled_by": "026a6d28-c22e-4aab-a8b4-bd7131a8ea35",
            "dependencies": [],
            "job_number": 0,
            "id": "497f6eca-6276-4993-bfeb-53cbbbba6f08",
            "started_at": "2019-08-24T14:15:22Z",
            "name": "string",
            "approved_by": "02030314-b162-4b4d-8af1-88eabdcc615d",
            "project_slug": "gh/CircleCI-Public/api-preview-docs",
            "status": "success",
            "type": "build",
            "stopped_at": "2019-08-24T14:15:30Z",
            "approval_request_id": "47bbf9d9-0b01-4281-9b67-9324ae3d0dff",
        }
        job = data_driver._to_job(raw_job_data)
        assert isinstance(job, Job)
        assert job.external_id == "497f6eca-6276-4993-bfeb-53cbbbba6f08"
        assert job.status == "success"
        assert job.started_at == datetime(2019, 8, 24, 14, 15, 22)
        assert job.stopped_at == datetime(2019, 8, 24, 14, 15, 30)
        assert job.workflow == workflow

    @patch(
        "services.fetch_data.datasources.circleci.CircleCIDataDriver._to_pipeline",
        return_value="pipeline",
    )
    def test_to_db_representation_routing(self, mock_to_pipeline):
        data_driver = CircleCIDataDriver()
        some_data = {"some": "data"}
        r = data_driver.to_db_representation(some_data, Pipeline)
        assert r == "pipeline"
        mock_to_pipeline.assert_called_with(some_data)
