import logging
import logging.config
from pathlib import Path
from typing import Callable

import uvicorn
import yaml
from fastapi import FastAPI, Request, Response, status
from fastapi.middleware import cors

from api import routes
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

# ПРИВЕТ ДОРОГОЙ РЕВЬЮВЕР !!

# Ты видишь мою реализацию проектоного задания
# Я очень жду замечаний от тебя - особенно бэст практис =)
# Прошу проверить работу с пристрастием ;)

# Сейчас я пишу unit-тесты, но решил отправить работу,
# чтобы за одно поправить замечания

# Большое спасибо за твою работу!
