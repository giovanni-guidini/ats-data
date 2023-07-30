from sqlalchemy import Column, ForeignKey, types
from sqlalchemy.orm import relationship

from database.models.base import Base


class Workflow(Base):
    __tablename__ = "workflows"

    id = Column("id", types.Integer, primary_key=True)
    external_id = Column(types.String, nullable=True)
    name = Column(types.String)
    started_at = Column(types.DateTime)
    stopped_at = Column(types.DateTime)
    status = Column(types.String)
    pipeline_id = Column("pipeline_id", types.Integer, ForeignKey("pipelines.id"))
    pipeline = relationship("Pipeline", back_populates="workflows")
    jobs = relationship("Job", back_populates="workflow")
