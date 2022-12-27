from fastapi import FastAPI
from fastapi.middleware import cors

from api import routes
from core.utils import read_config
from models.config_models import WebapiConfig

web_api: FastAPI = FastAPI()


def create_api():
    cfg = WebapiConfig(**read_config().get('webapi'))
    web_api.add_middleware(cors.CORSMiddleware,
                           allow_credentials=cfg.cors.credentials,
                           allow_headers=cfg.cors.headers,
                           allow_methods=cfg.cors.methdods,
                           allow_origins=cfg.cors.origins)

    web_api.include_router(routes.router, prefix=cfg.prefix)    # type: ignore

    return web_api
