from unittest.mock import MagicMock, call, patch

import pytest

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
                "id": "already_there",
                "name": "build-and-test",
                "status": "success",
                "pipeline_number": "25",
                "created_at": "2019-08-24T14:15:22Z",
                "stopped_at": "2019-08-24T14:15:22Z",
            },
            {
                "pipeline": pipeline,
                "pipeline_id": "5034460f-c7c4-4c43-9457-de07e2029e7b",
                "id": "already_there_needs_update",
                "name": "build-and-test",
                "status": "success",
                "pipeline_number": "25",
                "created_at": "2019-08-24T14:15:22Z",
                "stopped_at": "2019-08-24T14:15:22Z",
            },
            {
                "pipeline": pipeline,
                "pipeline_id": "5034460f-c7c4-4c43-9457-de07e2029e7b",
                "id": "new_workflow",
                "name": "build-and-test",
                "tag": "setup",
                "status": "success",
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

    @pytest.mark.asyncio
    @patch("services.fetch_data.FetchDataService._sync_model")
    async def test_sync_pipelines(self, mock_sync_model, dbsession):
        # Mock the data source and data drivers
        mock_datasource = MagicMock(name="datasource")
        mock_data_driver = MagicMock(name="data_driver")
        mock_datasource.data_driver = mock_data_driver
        # Create fake data to be the pipelines
        mock_pipelines = [
            MagicMock(name="pipeline_1"),
            MagicMock(name="pipeline_2"),
            MagicMock(name="pipeline_3"),
        ]
        mock_pipeline_1, mock_pipeline_2, mock_pipeline_3 = mock_pipelines
        # Fake the sync_model
        mock_sync_model.side_effect = [[mock_pipeline_1], [mock_pipeline_3]]
        # The function yields pages of pipeline raw_data
        async def get_pipelines_mock(*args, **kwargs):
            for page in [[mock_pipeline_1, mock_pipeline_2], [mock_pipeline_3]]:
                yield page

        mock_project_pipelines = MagicMock(side_effect=get_pipelines_mock)
        mock_datasource.get_all_project_pipelines = mock_project_pipelines

        fetch_data_service = FetchDataService(dbsession, {})
        synced_pipelines = await fetch_data_service.sync_pipelines(
            project=MagicMock(name="project"), datasource=mock_datasource
        )
        assert synced_pipelines == [mock_pipeline_1, mock_pipeline_3]
        # Assert that the sync was done correctly
        assert mock_sync_model.call_count == 2
        mock_sync_model.assert_has_calls(
            [
                call(
                    [mock_pipeline_1, mock_pipeline_2],
                    models.Pipeline,
                    mock_data_driver,
                    [UpdateFields("status", "state")],
                ),
                call(
                    [mock_pipeline_3],
                    models.Pipeline,
                    mock_data_driver,
                    [UpdateFields("status", "state")],
                ),
            ]
        )

    @pytest.mark.asyncio
    @patch("services.fetch_data.FetchDataService._sync_model")
    async def test_sync_workflows(self, mock_sync_model, dbsession):
        # Mock the data source and data drivers
        mock_datasource = MagicMock(name="datasource")
        mock_data_driver = MagicMock(name="data_driver")
        mock_datasource.data_driver = mock_data_driver
        # Create fake data to be the workflows
        mock_workflows = [
            MagicMock(name="workflow_1"),
            MagicMock(name="workflow_2"),
            MagicMock(name="workflow_3"),
        ]
        mock_workflow_1, mock_workflow_2, mock_workflow_3 = mock_workflows
        # Fake the sync_model
        mock_sync_model.side_effect = [[mock_workflow_1], [mock_workflow_3]]
        # The function yields pages of workflow raw_data
        async def get_workflows_mock(*args, **kwargs):
            for page in [[mock_workflow_1, mock_workflow_2], [mock_workflow_3]]:
                yield page

        mock_project_workflows = MagicMock(side_effect=get_workflows_mock)
        mock_datasource.get_pipeline_workflows = mock_project_workflows

        fetch_data_service = FetchDataService(dbsession, {})
        synced_workflows = await fetch_data_service.sync_workflows(
            pipeline=MagicMock(name="pipeline"), datasource=mock_datasource
        )
        assert synced_workflows == [mock_workflow_1, mock_workflow_3]
        # Assert that the sync was done correctly
        assert mock_sync_model.call_count == 2
        mock_sync_model.assert_has_calls(
            [
                call(
                    [mock_workflow_1, mock_workflow_2],
                    models.Workflow,
                    mock_data_driver,
                    [
                        UpdateFields("status", "status"),
                        UpdateFields("stopped_at", "stopped_at"),
                    ],
                ),
                call(
                    [mock_workflow_3],
                    models.Workflow,
                    mock_data_driver,
                    [
                        UpdateFields("status", "status"),
                        UpdateFields("stopped_at", "stopped_at"),
                    ],
                ),
            ]
        )
