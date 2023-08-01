from sqlalchemy import Column, ForeignKey, types
from sqlalchemy.orm import relationship

from database.models.base import Base


class Job(Base):
    __tablename__ = "jobs"

    id = Column("id", types.Integer, primary_key=True)
    external_id = Column(types.String, nullable=True)
    number = Column(types.Integer, nullable=False)
    status = Column(types.String)
    name = Column(types.String)
    started_at = Column(types.DateTime)
    stopped_at = Column(types.DateTime)
    workflow_id = Column("workflow_id", types.Integer, ForeignKey("workflows.id"))
    workflow = relationship("Workflow", back_populates="jobs")

    @property
    def duration(self):
        return self.stopped_at - self.started_at
