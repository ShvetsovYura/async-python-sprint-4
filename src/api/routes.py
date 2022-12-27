from fastapi import APIRouter, Response, status

router = APIRouter()


@router.get('/ping')
async def get_health_db():
    pass


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
