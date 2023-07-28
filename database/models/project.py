from sqlalchemy import Column, types, ForeignKey
from database.models.base import Base
from sqlalchemy.orm import relationship

class Project(Base):
    __tablename__ = 'projects'
    id = Column(types.BigInteger, primary_key=True)
    git_provider = Column(types.String)
    organization_id = Column('organization_id', types.BigInteger, ForeignKey('organizations.id'))
    organization = relationship('Organization', back_populates='projects')
    pipelines = relationship('Pipeline', back_populates='project')
