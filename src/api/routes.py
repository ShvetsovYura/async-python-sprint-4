import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status

from core.utils import read_config
from db.pg_source import PgDbSource
from models.config_models import DbConfig
from models.request_models import CreateShortLinkModel
from services.db import DbService

router = APIRouter()

# хотелось бы конечно все это заветнуть в класс
# c роутами, чтобы инкапсулировать логику,
# но незнаю как в FastAPI делать классы для endpoint'ов

db_source = PgDbSource(db_config=DbConfig(**read_config().get('db')))
db_srv = DbService(db_source=db_source)


def get_random_uuid() -> str:
    return str(uuid.uuid4())[-4:]


@router.get('/ping')
async def get_health_db():
    result = await db_srv.check_db()
    return {'db_connection': result}


@router.post('/', status_code=status.HTTP_201_CREATED)
async def create_short_link(
        link: CreateShortLinkModel,
        get_url_id: str = Depends(get_random_uuid)    # noqa B008
):
    await db_srv.create_link(url_id=get_url_id, original_url=link.original_link)


@router.get('/{url_id}', status_code=status.HTTP_307_TEMPORARY_REDIRECT)
async def redirect_by_short_link(url_id: str, response: Response):
    result = await db_srv.get_original_by_short(url_id)

    if result and isinstance(result, list):
        if not result[0]['active']:
            raise HTTPException(status_code=status.HTTP_410_GONE, detail='Link deactivated')
        original_link = result[0]['original_url']
        response.headers['Location'] = original_link

    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Link not found')


@router.delete('/{url_id}', status_code=status.HTTP_200_OK)
async def deactivate_link(url_id):
    result = await db_srv.deactivate_link(url_id)

    if result and isinstance(result, int):
        return {'updated': result}

    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Link not found')


@router.get('/{url_id}/status')
async def get_status(
        url_id: str,
        full_info: bool = Query(False, alias='full-info'),    # noqa B008
        skip: int = Query(0, alias='offset'),    # noqa B008
        limit: int = Query(10, alias='max-result')    # noqa B008
):

    return {'ok': 'query'}


@router.get('/health')
async def health():
    return {'status': 'up'}


@router.get('/redirect', status_code=status.HTTP_307_TEMPORARY_REDIRECT)
async def retirect_to_url(response: Response):
    response.headers['Location'] = 'https://ya.ru'
