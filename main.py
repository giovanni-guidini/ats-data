import asyncio

from config import load_config
from database.engine import get_dbsession
from database.models.enums import CiProviders, GitProviders
from database.models.organization import Organization
from database.models.pipeline import Pipeline
from database.models.project import Project
from services.fetch_data import FetchDataService


async def main():

    config = load_config()

    dbsession = get_dbsession()

    organization = Organization(name="codecov")
    dbsession.add(organization)

    project = Project(
        ci_provider=CiProviders.circleci,
        git_provider=GitProviders.github,
        name="shared",
        organization=organization,
    )
    dbsession.add(project)

    dbsession.flush()

    fetch_service = FetchDataService(dbsession, config)
    await fetch_service.sync_project(project)

    print("Finished syncing project data")

    # TODO: Actually save info in the DB
    dbsession.commit()


if __name__ == "__main__":
    asyncio.run(main())
