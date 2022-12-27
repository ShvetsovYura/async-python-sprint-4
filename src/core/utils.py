import base64
import logging
import logging.config
import os
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger(__name__)


def get_root_path() -> Path:
    """ Получает корневой путь к проекту """
    return Path(__file__).resolve().parent


def get_config_path():
    """ Получает путь конфигу"""
    relative_path = os.environ.get('CONFIG_RELATIVE_PATH') or '../app-config.yml'
    return Path.joinpath(get_root_path(), relative_path)


class ConfigReader:
    """
    Кэширующий класс
    Проверяет, если конфиг уже был считан с диска, то отдает этот конфиг
    иначе пытается прочитать опять
    """

    def __init__(self) -> None:
        self._app_config = None

    def __call__(self, *args: Any, **kwds: Any) -> Any:
        if not self._app_config:
            with open(get_config_path()) as stream:
                self._app_config = yaml.safe_load(stream)
        return self._app_config


config_reader = ConfigReader()


def read_config():
    return config_reader()


def config_logger():
    config = read_config()
    logging.config.dictConfig(config.get('logging'))


def base64_decode(base64_string: str) -> str:
    return base64.b64decode(base64_string).decode(encoding='UTF-8')


def check_file_exists(path: Path):
    if path.exists():
        return True
    return False
