import uuid

from fastapi import APIRouter, Depends, HTTPException, Response, status

from core.utils import read_config
from db.source import DbSource
from models.config_models import DbConfig
from models.request_models import CreateShortLinkModel
from services.db import DbService

router = APIRouter()

# хотелось бы конечно все это заветнуть в класс
# c роутами, чтобы инкапсулировать логику,
# но незнаю как в FastAPI делать классы для endpoint'ов

db_source = DbSource(db_config=DbConfig(**read_config().get('db')))
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
    await db_srv.create_link(url_id=get_url_id,
                             short_url=get_url_id,
                             original_url=link.original_link)


@router.get('/{url_id}', status_code=status.HTTP_307_TEMPORARY_REDIRECT)
async def redirect_by_short_link(url_id: str, response: Response):
    result = await db_srv.get_original_by_short(url_id)

    if result and isinstance(result, list):
        original_link = result[0]['original_url']
        response.headers['Location'] = original_link

    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Link not found')


# @router.get('/<url_id>/status?[full-info]&&[max-result=10]&&[offset=0]')
# async def get_status():
#     pass


@router.get('/health')
async def health():
    return {'status': 'up'}


@router.get('/redirect', status_code=status.HTTP_307_TEMPORARY_REDIRECT)
async def retirect_to_url(response: Response):
    response.headers['Location'] = 'https://ya.ru'
