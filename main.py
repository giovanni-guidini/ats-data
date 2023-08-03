import asyncio
import logging

from config import load_config
from database import models
from database.engine import get_dbsession
from database.models.enums import CiProviders, GitProviders
from services.fetch_data import FetchDataService
from services.process_data import ProcessDataService
from utils.logging_config import LOGGER_NAME, configure_logger

logger = logging.getLogger(LOGGER_NAME)


async def collect_data(config, dbsession, project):
    fetch_service = FetchDataService(dbsession, config)
    await fetch_service.sync_project(project)

    logger.info("Finished syncing project data")
    dbsession.flush()


def process_data(config, dbsession, project):
    process_service = ProcessDataService(dbsession, config)
    process_service.sync_project_metrics(project)

    logger.info("Finished processing data")
    dbsession.flush()

    logger.info("Generating Workflow data plot")
    process_service.plot_workflow_durations(project)


def create_base_classes(dbsession):
    organization = models.Organization(name="codecov")
    dbsession.add(organization)

    project = models.Project(
        ci_provider=CiProviders.circleci,
        git_provider=GitProviders.github,
        name="worker",
        organization=organization,
        label_analysis_job_name="ATS",
        regular_tests_job_name="test",
    )
    dbsession.add(project)
    dbsession.flush()

    return project


async def main():

    configure_logger(logger=logger)
    config = load_config()

    dbsession = get_dbsession()

    project = (
        dbsession.query(models.Project).filter(models.Project.name == "worker").first()
    )
    if project is None:
        project = create_base_classes(dbsession)

    await collect_data(config, dbsession, project)

    process_data(config, dbsession, project)

    # TODO: Actually save info in the DB
    dbsession.commit()

    logger.info("=> Project totals")
    print(project.totals)


if __name__ == "__main__":
    asyncio.run(main())
