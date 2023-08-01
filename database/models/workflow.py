from sqlalchemy import Column, ForeignKey, types
from sqlalchemy.orm import relationship, Mapped

from database.models.base import Base
from database.models.pipeline import Pipeline


class Workflow(Base):
    __tablename__ = "workflows"

    id = Column("id", types.Integer, primary_key=True)
    external_id = Column(types.String, nullable=True)
    name = Column(types.String)
    started_at = Column(types.DateTime)
    stopped_at = Column(types.DateTime)
    status = Column(types.String)
    label_analysis_duration_seconds = Column(types.Integer, nullable=True)
    label_analysis_success = Column(types.Boolean, nullable=True)
    regular_tests_duration_seconds = Column(types.Integer, nullable=True)
    regular_tests_success = Column(types.Boolean, nullable=True)

    # Relationships
    pipeline_id = Column("pipeline_id", types.Integer, ForeignKey("pipelines.id"))
    pipeline: Mapped[Pipeline] = relationship("Pipeline", back_populates="workflows")
    jobs = relationship("Job", back_populates="workflow")

    @property
    def label_analysis_job_name(self):
        return self.pipeline.label_analysis_job_name

    @property
    def regular_tests_job_name(self):
        return self.pipeline.regular_tests_job_name
