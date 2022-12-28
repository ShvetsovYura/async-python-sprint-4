import logging
import logging.config
from pathlib import Path

import uvicorn
import yaml

from core.api import create_api
from core.utils import read_config
from models.config_models import WebapiConfig

logger = logging.getLogger(__name__)

if __name__ == '__main__':

    with open(Path.cwd() / 'src/log-config.yml', 'r') as stream:
        cfg_ = yaml.safe_load(stream)
        logging.config.dictConfig(cfg_.get('logging'))

    # # asyncio.run(start_webserver()) # noqa E800

    api = create_api()    # noqa F841 # noqa E800
    cfg = WebapiConfig(**read_config().get('webapi'))    # noqa E800
    uvicorn.run('core.api:web_api', port=cfg.port)    # noqa E800
