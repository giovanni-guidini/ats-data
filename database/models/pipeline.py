from sqlalchemy import Column, ForeignKey, types
from sqlalchemy.orm import relationship

from database.models.base import Base


class Pipeline(Base):
    __tablename__ = "pipelines"

    id = Column("id", types.Integer, primary_key=True)
    external_id = Column(types.String, nullable=True)
    number = Column(types.Integer, nullable=False)
    status = Column(types.String)
    created_at = Column(types.DateTime)
    project_id = Column("project_id", types.Integer, ForeignKey("projects.id"))
    project = relationship("Project", back_populates="pipelines")
    workflows = relationship("Workflow", back_populates="pipeline")
