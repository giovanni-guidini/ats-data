from database.models.enums import CiProviders
from services.fetch_data.datasources.base import BaseDatasource
from services.fetch_data.datasources.circleci import CircleCIDatasource


def get_datasource_class(ci_provider: CiProviders) -> BaseDatasource:
    lookup_table = {CiProviders.circleci: CircleCIDatasource}
    return lookup_table.get(ci_provider)
