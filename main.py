import asyncio
from database.engine import get_dbsession
from config import load_config
from database.models.pipeline import Pipeline
from services.fetch_data.datasources.circleci import CircleCIDatasource
from datetime import datetime

def circleci_to_pipeline(dbsession, runs_info: dict):
    for pipeline in runs_info.get('items', []):
        obj = Pipeline()
        obj.pipeline_id = pipeline['id']
        obj.created_at = datetime.fromisoformat(pipeline['created_at'][:19])
        obj.status = pipeline['state']
        obj.run_number = pipeline['number']
        dbsession.add(obj)

async def main():

    config = load_config()
    circleci = CircleCIDatasource(config=config)

    dbsession = get_dbsession()

    runs_info = await circleci.get_all_project_pipelines('gh/codecov/shared')
    circleci_to_pipeline(dbsession, runs_info)
    dbsession.flush()
    
    saved_info = dbsession.query(Pipeline).all()
    # TODO: Actually save info in the DB
    

if __name__ == "__main__":
    asyncio.run(main())
