import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status

from core.utils import read_config
from db.pg_source import PgDbSource
from models.config_models import DbConfig
from models.request_models import CreateShortLinkModel
from services.db import DbService

logger = logging.getLogger(__name__)

router = APIRouter()

db_source = PgDbSource(db_config=DbConfig(**read_config().get('db')))
db_srv = DbService(db_source=db_source)


def get_random_uuid() -> str:
    return str(uuid.uuid4())[-4:]


@router.get('/ping', summary='Опрос доступности БД')
async def get_health_db():
    """
    Проверка, доступна ли БД для работы
    """

    result = await db_srv.check_db()
    return {'db_connection': result}


@router.post('/', status_code=status.HTTP_201_CREATED, summary='Создание короткой ссылки')
async def create_short_link(
        link: CreateShortLinkModel,
        get_url_id: str = Depends(get_random_uuid)    # noqa B008
):
    """
    Создание коротокой ссылки из переаднной оригинальной
    """

    await db_srv.create_link(url_id=get_url_id, original_url=link.original_link)


@router.get('/{url_id}',
            status_code=status.HTTP_307_TEMPORARY_REDIRECT,
            summary='Переход к оригинальой ссылке по идентификатору короткой')
async def redirect_by_short_link(    # noqa CCR001
        url_id: str, response: Response, request: Request):
    """
    Клиент редиректится на оригинальную ссылку при перехаоде на короткую,
    если соответствие найдено в БД.
    В противном случае будет ошибка 404
    """

    result = await db_srv.get_original_by_short(url_id)

    if result and isinstance(result, list):
        try:

            # не надо падать, когда вдруг не можем записать статистику
            client = request.client
            await db_srv.add_statistic(url_id=url_id,
                                       info=f'host: {client.host if client else "" }')
        except Exception as e:    # noqa B902
            logger.exception(e)

        if not result[0]['active']:
            raise HTTPException(status_code=status.HTTP_410_GONE, detail='Link deactivated')
        original_link = result[0]['original_url']
        response.headers['Location'] = original_link
        return {'action': 'redirected'}

    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Link not found')


@router.delete('/{url_id}',
               status_code=status.HTTP_200_OK,
               summary='Удаление сопоставления кортокой и оригинальной ссылок')
async def deactivate_link(url_id):
    """
    Деактивируется кортокая ссылка и при переходе по ней в дальнейшем
    не будет происходить редирект на оригинальную ссылку
    """

    result = await db_srv.deactivate_link(url_id)

    if result and isinstance(result, int):
        return {'updated': result}

    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Link not found')


@router.get('/{url_id}/status', summary='Получение статистики перехода по коротким ссылкам')
async def get_status(
    url_id: str,
    full_info: bool = Query(    # noqa B008
        default=False,
        alias='full-info',
        description='Показывать полную статиситку'),
    skip: int = Query(    # noqa B008 
        default=0, alias='offset', description='Сколько записей пропустить'),
    limit: int = Query(    # noqa B008
        default=10,
        alias='max-result',
        description='Сколько записей показывать при подробном отображении')):
    """
    Получение полной или общей статистики по переходам по коротким ссылкам
    """

    result_count = await db_srv.get_stats_count_by_id(url_id)
    answer = {}
    if result_count and isinstance(result_count, list):
        answer['url_id'] = url_id
        answer['count'] = result_count[0]['count']

    if full_info:
        add_info = await db_srv.get_stats_by_url_id(url_id=url_id, limit=limit, offset=skip)
        answer['add_info'] = add_info
    return answer


@router.get('/health', summary='Доступен web-сервис или нет')
async def health():
    return {'status': 'up'}
