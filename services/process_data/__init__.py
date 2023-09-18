import statistics
from datetime import datetime
from typing import List, Union

import matplotlib.pyplot as plt
import numpy as np
from sqlalchemy.orm import lazyload

from database import models


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
        stdev_duration = statistics.pstdev(durations) if len(durations) > 1 else None
        deciles = (
            statistics.quantiles(durations, n=10, method="inclusive")
            if len(durations) > 1
            else None
        )
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
        totals.label_analysis_success_count = len(label_analysis_success)
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
        totals.regular_tests_success_count = len(regular_tests_success)
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

    def plot_workflow_durations(self, project: models.Project):
        # Get all the workflows for a project
        pipeline_id_rows = (
            self.dbsession.query(models.Pipeline.id)
            .filter(models.Pipeline.project_id == project.id)
            .all()
        )
        pipeline_ids = [row[0] for row in pipeline_id_rows]
        workflows = (
            self.dbsession.query(models.Workflow)
            .options(lazyload(models.Workflow.jobs))
            .filter(models.Workflow.pipeline_id.in_(pipeline_ids))
            .all()
        )
        # Sort by date
        workflows.sort(key=lambda item: item.started_at)
        # Extract data for plotting
        dates = [workflow.started_at for workflow in workflows]
        label_analysis_durations = [
            workflow.label_analysis_duration_seconds for workflow in workflows
        ]
        regular_tests_durations = [
            workflow.regular_tests_duration_seconds for workflow in workflows
        ]

        # Convert dates to a more suitable format for plotting (e.g., matplotlib's internal date representation)
        dates_numeric = [datetime.timestamp(date) for date in dates]

        zipped_data = zip(
            dates_numeric, label_analysis_durations, regular_tests_durations
        )
        zipped_data = list(
            filter(
                lambda item: item[0] is not None
                and item[1] is not None
                and item[2] is not None,
                zipped_data,
            )
        )

        dates_numeric = [item[0] for item in zipped_data]
        label_analysis_durations = [item[1] for item in zipped_data]
        regular_tests_durations = [item[2] for item in zipped_data]

        # Create a new figure and set axis labels
        plt.figure(figsize=(10, 6))
        plt.xlabel("Date")
        plt.ylabel("Duration (seconds)")

        # Plot the data
        plt.scatter(
            dates_numeric, label_analysis_durations, marker="o", label="Label Analysis"
        )
        plt.scatter(
            dates_numeric, regular_tests_durations, marker="o", label="Regular Tests"
        )
        # Calculate trend lines
        label_analysis_trend = np.polyfit(dates_numeric, label_analysis_durations, 5)
        plottable_trend = np.poly1d(label_analysis_trend)
        plt.plot(dates_numeric, plottable_trend(dates_numeric))

        regular_tests_trend = np.polyfit(dates_numeric, regular_tests_durations, 5)
        plottable_trend = np.poly1d(regular_tests_trend)
        plt.plot(dates_numeric, plottable_trend(dates_numeric))

        # Add a legend
        plt.legend()

        # Set the x-axis ticks as dates
        # Aggregate dates that are less than 1d appart
        label_ticks = [datetime.fromtimestamp(dates_numeric[0])]
        numeric_ticks = [dates_numeric[0]]
        TWELVE_HOURS = 12 * 60 * 60
        for date in dates_numeric[1:]:
            if (datetime.fromtimestamp(date) - label_ticks[-1]).seconds >= TWELVE_HOURS:
                label_ticks.append(datetime.fromtimestamp(date))
                numeric_ticks.append(date)
        plt.xticks(
            numeric_ticks,
            [date.strftime("%Y-%m-%D") for date in label_ticks],
            rotation=45,
            ha="right",
        )

        # Set a title
        plt.title("Label Analysis vs Regular Tests Durations Over Time")
        plt.suptitle(
            f"{project.organization.name}/{project.name} - {project.ci_provider.value}"
        )

        # Show the plot
        plt.tight_layout()
        plt.show()
