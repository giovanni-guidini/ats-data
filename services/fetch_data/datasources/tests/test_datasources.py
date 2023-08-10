import pytest

from database.models.enums import CiProviders
from services.fetch_data.datasources import get_datasource_class
from services.fetch_data.datasources.circleci import CircleCIDatasource


@pytest.mark.parametrize(
    "ci_provider,expected_class",
    [(CiProviders.circleci, CircleCIDatasource), ("not ci provider", None)],
)
def test_get_datasource_class(ci_provider, expected_class):
    assert get_datasource_class(ci_provider) == expected_class
