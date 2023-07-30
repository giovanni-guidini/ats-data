from datetime import datetime
from uuid import uuid4

import factory
from factory import Factory

from database import models
from database.models.enums import CiProviders, GitProviders


class OrganizationFactory(Factory):
    class Meta:
        model = models.Organization

    name = factory.Faker("name")


class ProjectFactory(Factory):
    class Meta:
        model = models.Project

    git_provider = GitProviders.github
    name = factory.Faker("name")
    ci_provider = CiProviders.circleci
    organization = factory.SubFactory(OrganizationFactory)


class PipelineFactory(Factory):
    class Meta:
        model = models.Pipeline

    external_id = factory.LazyFunction(lambda: str(uuid4()))
    created_at = datetime(2023, 7, 30)
    project = factory.SubFactory(ProjectFactory)


class WorkflowFactory(Factory):
    class Meta:
        model = models.Workflow

    external_id = factory.LazyFunction(lambda: str(uuid4()))
    started_at = datetime(2023, 7, 30, 10)
    stopped_at = datetime(2023, 7, 30, 11)
    pipeline = factory.SubFactory(PipelineFactory)
