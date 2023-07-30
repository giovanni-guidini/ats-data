import database.models as models
from database.engine import engine
from database.models.base import Base


def run_migrations() -> None:
    # TODO: Add a migration manager
    # Possibly https://alembic.sqlalchemy.org/en/latest/index.html
    Base.metadata.create_all(engine)


if __name__ == "__main__":
    run_migrations()
