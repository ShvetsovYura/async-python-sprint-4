import logging
import logging.config
from pathlib import Path
from typing import Callable

import uvicorn
import yaml
from fastapi import FastAPI, Request, Response, status
from fastapi.middleware import cors

from api.v1 import routes
from core.utils import read_config
from models.config_models import WebapiConfig

logger = logging.getLogger(__name__)

config = read_config()
cfg = WebapiConfig(**config.get('webapi'))
app: FastAPI = FastAPI()

app.include_router(routes.router, prefix=cfg.prefix)
app.add_middleware(cors.CORSMiddleware,
                   allow_credentials=cfg.cors.credentials,
                   allow_headers=cfg.cors.headers,
                   allow_methods=cfg.cors.methdods,
                   allow_origins=cfg.cors.origins)


@app.middleware('http')
async def check_client_subnet(request: Request, call_next: Callable):

    if request.client:
        for subnet_ in config.get('subnet_blacklist', []):
            if subnet_ in request.client.host:
                return Response(status_code=status.HTTP_403_FORBIDDEN,
                                content='Запрещено для этой подсети')

    return await call_next(request)


if __name__ == '__main__':

    with open(Path.cwd() / 'src/log-config.yml', 'r') as stream:
        cfg_ = yaml.safe_load(stream)
        logging.config.dictConfig(cfg_.get('logging'))

    uvicorn.run('main:app', port=cfg.port)    # noqa E800

# ЗАМЕЧАНИЯ

# src/api/routes.py: 18
# И так хорошо :) Единственное, что нужно сделать - это версионирование ардесов эндпоинтов и папок
#  в проекте. Т.к. тут должно быть в структуре папок api/v1/routes
# Result: Done! Изменил структуру

# src/api/routes: 34
# Swagger документация сервисов выглядит максимально куцей, давай добавим хотя бы description,
# подробнее тут: https://fastapi.tiangolo.com/tutorial/path-operation-configuration/?h=description#summary-and-description # noqa E501
# Result: Done! Добавил описания к endpoint'ам

# src/api/routes: 39
# Тут, кажется, будет логично вернуть пользователю созданную ссылку в теле ответа.
# Result: Done! Добавил модель ответа CreatedLinkModel, где содержатся ссылки

# src/api/router: 54
# Крайне рекомендуется избегать использования такого "широкого" исключения.
# Отличным вариантом будет создание какого-нибудь кастомного исключения и дальнейший перехват его.
# https://docs.python.org/3/library/exceptions.html#exception-hierarchy
# Result: Done! Ловлю кастомные ошибки
