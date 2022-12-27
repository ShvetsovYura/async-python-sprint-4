from fastapi import APIRouter, Response, status

from core.utils import read_config
from db.source import DbSource
from models.config_models import DbConfig
from services.db import DbService

router = APIRouter()

# хотелось бы конечно все это заветнуть в класс
# c роутами, чтобы инкапсулировать логику,
# но незнаю как в FastAPI делать классы для endpoint'ов

db_source = DbSource(db_config=DbConfig(**read_config().get('db')))
db_srv = DbService(db_source=db_source)


@router.get('/ping')
async def get_health_db():
    result = await db_srv.check_db()

    return {'db_connection': result}


@router.post('/')
async def create_short_link():
    pass


# @router.get('/{url_id}')
# async def redirect_by_short_link():
#     pass

# @router.get('/<url_id>/status?[full-info]&&[max-result=10]&&[offset=0]')
# async def get_status():
#     pass


@router.get('/health')
async def health():
    return {'status': 'up'}


@router.get('/redirect', status_code=status.HTTP_307_TEMPORARY_REDIRECT)
async def retirect_to_url(response: Response):
    response.headers['Location'] = 'https://ya.ru'
