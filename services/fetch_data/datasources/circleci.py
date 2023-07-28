from typing import Dict
from services.fetch_data.datasources.base import BaseDatasource
from services.fetch_data.datasources.error import DatasourceConfigError

from config import get_config
import httpx

class CircleCIDatasource(BaseDatasource):
    BASE_URL = 'https://circleci.com/api/v2'
    def __init__(self, config: Dict):
        self.api_token = get_config(config, 'datasources', 'circleci', 'api_token')
        
        if self.api_token is None:
            raise DatasourceConfigError('Missing API TOKEN')
        
    async def _execute_request(self, method: str, url: str, headers: dict = None, params: dict = None):
        async with httpx.AsyncClient(base_url=self.BASE_URL) as client:
            response = await client.request(method, url, headers=headers, params=params)
            print(response)
            return response.json()
        # TODO: Handle errors and such
        
    async def get_all_project_pipelines(self, project_slug: str):
        # Get a list of all project's pipelines
        # https://circleci.com/docs/api/v2/index.html#operation/listPipelinesForProject
        headers = {
            'Circle-Token': self.api_token,
        }
        url = f'/project/{project_slug}/pipeline'

        response = await self._execute_request('GET', url, headers=headers)
        return response