from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database.models.base import Base

engine = create_engine("sqlite:///.sqlite", echo=True)
_Session = sessionmaker(bind=engine)

_session = _Session()


def get_dbsession():
    return _session
