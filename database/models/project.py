from enum import Enum

from sqlalchemy import Column, ForeignKey, types
from sqlalchemy.orm import relationship

from database.models.base import Base
from database.models.enums import CiProviders, GitProviders


class Project(Base):
    __tablename__ = "projects"

    id = Column("id", types.Integer, primary_key=True)
    git_provider = Column(types.Enum(GitProviders))
    name = Column(types.String)
    ci_provider = Column(types.Enum(CiProviders))
    organization_id = Column(
        "organization_id", types.BigInteger, ForeignKey("organizations.id")
    )
    organization = relationship("Organization", back_populates="projects")
    pipelines = relationship("Pipeline", back_populates="project")
