import logging
import logging.config
from pathlib import Path
from typing import Callable

import uvicorn
import yaml
from fastapi import FastAPI, Request, Response, status
from fastapi.middleware import cors

from api.v1.routes import router
from core.utils import read_config
from models.config_models import WebapiConfig

logger = logging.getLogger(__name__)

config = read_config()
cfg = WebapiConfig(**config.get('webapi'))
app: FastAPI = FastAPI()

app.include_router(router, prefix=cfg.prefix)
app.add_middleware(cors.CORSMiddleware,
                   allow_credentials=cfg.cors.credentials,
                   allow_headers=cfg.cors.headers,
                   allow_methods=cfg.cors.methods,
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

    uvicorn.run('main:app', host='0.0.0.0', port=cfg.port)    # noqa E800

# Большое спасибо за ревью!! Хочу еще одно =)

# ЗАМЕЧАНИЯ
# Сделал контенеризацию (docker-compose)

# В следующем спринте применю Settings из pydantic =)

# src/services/db.py: 29
# Мы всегда расчитываем, на то, что проект будет развиваться.
# А в большом проекте работа с чистым sql крайне затруднительна.
# И в этой связи лучше сразу использовать ORM.
# https://fastapi.tiangolo.com/advanced/async-sql-databases/
# Более того, это позволит нам сильно упростить содержимое src/db

# Result: Я согласен, что с ORM работать проще!
# Но я реализовывал катомную работу с БД, т.е. не использовал сторонние либы
# для работы с БД. Поэтому не знаю как запихнуть мою реализацию в SQLAlchemy,
# чтобы исползовать ORM :(
# Если в моей реалзации как-то можно прикрутить ORM - буду только рад
# ------------------------------------------------------------------

# src/init_db_schema.sql
# Этот не самый надежный способ  создания и обновления таблиц БД.
# С развитием проекта структура будет меняться и без миграций будет практически не возможно поддерживать проект. # noqa E501
# Я уже писал выше про sqlalchemy, с ней очень ловко работает Alembic
# https://habr.com/ru/post/580866/

# Result: У меня нет ORM (попытался объяснить в предыдущем замечании).
# Как сделать без ORM - пока не знаю.

# src/api/routes.py: 18
# И так хорошо :) Единственное, что нужно сделать - это версионирование ардесов эндпоинтов и папок
#  в проекте. Т.к. тут должно быть в структуре папок api/v1/routes

# Result: Done! Изменил структуру
# ------------------------------------------------------------------

# src/api/routes.py: 34
# Swagger документация сервисов выглядит максимально куцей, давай добавим хотя бы description,
# подробнее тут: https://fastapi.tiangolo.com/tutorial/path-operation-configuration/?h=description#summary-and-description # noqa E501

# Result: Done! Добавил описания к endpoint'ам
# ------------------------------------------------------------------

# src/api/routes.py: 39
# Тут, кажется, будет логично вернуть пользователю созданную ссылку в теле ответа.

# Result: Done! Добавил модель ответа CreatedLinkModel, где содержатся ссылки
# ------------------------------------------------------------------

# src/api/routes.py: 54
# Крайне рекомендуется избегать использования такого "широкого" исключения.
# Отличным вариантом будет создание какого-нибудь кастомного исключения и дальнейший перехват его.
# https://docs.python.org/3/library/exceptions.html#exception-hierarchy

# Result: Done! Ловлю кастомные ошибки
# ------------------------------------------------------------------

# src/api/routes.py: 64
# Тут как и везде, не нужно забывать об указании типов принимаемых параметров.

# Result: Done! Добавил аннотаций
# ------------------------------------------------------------------

# src/api/routes.py: 83
# Эти параметры нужно валидировать

# Result: Done! Добавил валидации
# ------------------------------------------------------------------
