from sqlalchemy import Column, types
from database.models.base import Base
from sqlalchemy.orm import relationship

class Organization(Base):
    __tablename__ = 'organizations'
    id = Column(types.BigInteger, primary_key=True)
    name = Column(types.String)
    projects = relationship('Project', back_populates='organization')