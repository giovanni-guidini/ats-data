from database import models
from typing import List, Union
import statistics

from sqlalchemy.orm import lazyload


class ProcessDataService(object):
    def __init__(self, dbsession, config: dict = None) -> None:
        if config is None:
            config = {}
        self.config = config
        self.dbsession = dbsession

    def calculate_workflow_run_durations(self, workflow: models.Workflow):
        label_analysis_job = (
            self.dbsession.query(models.Job)
            .filter(
                models.Job.workflow_id == workflow.id,
                models.Job.name == workflow.label_analysis_job_name,
            )
            .first()
        )
        regular_tests_job = (
            self.dbsession.query(models.Job)
            .filter(
                models.Job.workflow_id == workflow.id,
                models.Job.name == workflow.regular_tests_job_name,
            )
            .first()
        )
        if label_analysis_job is None:
            print("LABEL ANALYSIS JOB MISSING")
        if regular_tests_job is None:
            print("REGULAR TESTS JOB MISSING")

        if label_analysis_job:
            workflow.label_analysis_success = label_analysis_job.status == "success"
            workflow.label_analysis_duration_seconds = (
                label_analysis_job.stopped_at - label_analysis_job.started_at
            ).seconds

        if regular_tests_job:
            workflow.regular_tests_success = regular_tests_job.status == "success"
            workflow.regular_tests_duration_seconds = (
                regular_tests_job.stopped_at - regular_tests_job.started_at
            ).seconds

        return dict(
            label_analysis_success=workflow.label_analysis_success,
            label_analysis_duration_seconds=workflow.label_analysis_duration_seconds,
            regular_tests_success=workflow.regular_tests_success,
            regular_tests_duration_seconds=workflow.regular_tests_duration_seconds,
        )

    def calculate_statistics(self, durations: List[int]) -> dict:
        mean_duration = statistics.mean(durations) if durations != [] else None
        median_duration = statistics.median(durations) if durations != [] else None
        stdev_duration = statistics.stdev(durations) if len(durations) > 1 else 0
        deciles = statistics.quantiles(durations, n=10) if len(durations) > 1 else None
        p90_duration = deciles[-1] if deciles else None
        return dict(
            mean_duration=mean_duration,
            median_duration=median_duration,
            stdev_duration=stdev_duration,
            p90_duration=p90_duration,
        )

    def calculate_totals(
        self,
        parent_model: Union[models.Pipeline, models.Project],
        workflow_run_durations: List[dict],
    ):
        totals = models.Totals()
        label_analysis_success = list(
            filter(
                lambda item: item["label_analysis_success"] == True,
                workflow_run_durations,
            )
        )
        label_analysis_fail = list(
            filter(
                lambda item: item["label_analysis_success"] == False,
                workflow_run_durations,
            )
        )
        label_analysis_success_durations = list(
            map(
                lambda item: item["label_analysis_duration_seconds"],
                label_analysis_success,
            )
        )
        totals.label_analysis_failure_count = len(label_analysis_success)
        totals.label_analysis_failure_count = len(label_analysis_fail)
        label_analysis_statistics = self.calculate_statistics(
            label_analysis_success_durations
        )
        totals.label_analysis_mean_duration = label_analysis_statistics["mean_duration"]
        totals.label_analysis_median_duration = label_analysis_statistics[
            "median_duration"
        ]
        totals.label_analysis_stdev_duration = label_analysis_statistics[
            "stdev_duration"
        ]
        totals.label_analysis_p90_duration = label_analysis_statistics["p90_duration"]

        regular_tests_success = list(
            filter(
                lambda item: item["regular_tests_success"] == True,
                workflow_run_durations,
            )
        )
        regular_tests_fail = list(
            filter(
                lambda item: item["regular_tests_success"] == False,
                workflow_run_durations,
            )
        )
        regular_tests_success_durations = list(
            map(
                lambda item: item["regular_tests_duration_seconds"],
                regular_tests_success,
            )
        )
        totals.regular_tests_failure_count = len(regular_tests_success)
        totals.regular_tests_failure_count = len(regular_tests_fail)
        regular_tests_statistics = self.calculate_statistics(
            regular_tests_success_durations
        )
        totals.regular_tests_mean_duration = regular_tests_statistics["mean_duration"]
        totals.regular_tests_median_duration = regular_tests_statistics[
            "median_duration"
        ]
        totals.regular_tests_stdev_duration = regular_tests_statistics["stdev_duration"]
        totals.regular_tests_p90_duration = regular_tests_statistics["p90_duration"]

        self.dbsession.add(totals)
        parent_model.totals = totals
        return totals

    def sync_project_metrics(self, project: models.Project):
        # Traverse the "tree" of pipelines and workflows in the project
        # And work our way up updating the data
        # We don't go down branches that are already calculated
        pipelines = (
            self.dbsession.query(models.Pipeline)
            .options(lazyload(models.Pipeline.workflows))
            .filter(models.Pipeline.project_id == project.id)
            .all()
        )
        project_workflow_runs = []
        for pipeline in pipelines:
            workflow_runs = []
            workflows = (
                self.dbsession.query(models.Workflow)
                .options(lazyload(models.Workflow.jobs))
                .filter(
                    models.Workflow.pipeline_id == pipeline.id,
                )
                .all()
            )
            for workflow in workflows:
                workflow_run_durations = self.calculate_workflow_run_durations(workflow)
                workflow_runs.append(workflow_run_durations)
            self.calculate_totals(pipeline, workflow_runs)
            project_workflow_runs.extend(workflow_runs)
        self.calculate_totals(project, project_workflow_runs)
