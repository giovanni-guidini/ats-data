from sqlalchemy import Column, types
from sqlalchemy.orm import relationship

from database.models.base import Base


class Organization(Base):
    __tablename__ = "organizations"

    id = Column("id", types.Integer, primary_key=True)
    name = Column(types.String)
    projects = relationship("Project", back_populates="organization")
