import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from database.models.base import Base


@pytest.fixture
def engine():
    engine = create_engine("sqlite:///:memory:", echo=False)
    return engine


@pytest.fixture
def db(engine):
    Base.metadata.create_all(engine)


@pytest.fixture
def dbsession(engine, db):
    connection = engine.connect()

    connection_transaction = connection.begin()

    # bind an individual Session to the connection
    session = Session(bind=connection)

    yield session

    session.close()
    connection_transaction.rollback()
    connection.close()
