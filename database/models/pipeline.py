from database.models.base import Base
from sqlalchemy import Column, ForeignKey, types
from sqlalchemy.orm import relationship

class Pipeline(Base):
    __tablename__ = "pipelines"
    id = Column(types.Integer, primary_key=True)
    pipeline_id = Column(types.String, nullable=False)
    run_number = Column(types.Integer, nullable=False)
    status = Column(types.String)
    workflow_name = Column(types.String)
    created_at = Column(types.DateTime)
    project_id = Column('project_id', types.Integer, ForeignKey('projects.id'))
    project = relationship('Project', back_populates='pipelines')

    def __repr__(self):
        return f"Pipeline<id='{self.id}', pipeline_id='{self.pipeline_id}', status='{self.status}'>"