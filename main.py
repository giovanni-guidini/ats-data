import asyncio

from config import load_config
from database.engine import get_dbsession
from database.models.enums import CiProviders, GitProviders
from database import models
from services.fetch_data import FetchDataService
from services.process_data import ProcessDataService


async def collect_data(config, dbsession, project):
    fetch_service = FetchDataService(dbsession, config)
    await fetch_service.sync_project(project)

    print("Finished syncing project data")
    dbsession.flush()


def process_data(config, dbsession, project):
    process_service = ProcessDataService(dbsession, config)
    process_service.sync_project_metrics(project)

    print("Finished processing data")
    dbsession.flush()


def create_base_classes(dbsession):
    organization = models.Organization(name="codecov")
    dbsession.add(organization)

    project = models.Project(
        ci_provider=CiProviders.circleci,
        git_provider=GitProviders.github,
        name="shared",
        organization=organization,
        label_analysis_job_name="labelanalysis",
        regular_tests_job_name="build-3.10.5",
    )
    dbsession.add(project)
    dbsession.flush()

    return project


async def main():

    config = load_config()

    dbsession = get_dbsession()

    project = dbsession.query(models.Project).first()
    if project is None:
        project = create_base_classes(dbsession)

    # await collect_data(config, dbsession, project)

    process_data(config, dbsession, project)

    # TODO: Actually save info in the DB
    # dbsession.commit()

    print("=> Project totals")
    print(project.totals)


if __name__ == "__main__":
    asyncio.run(main())
