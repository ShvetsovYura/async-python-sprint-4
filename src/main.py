import logging
import logging.config
from datetime import datetime, timedelta, timezone
from pathlib import Path

import uvicorn
import yaml

from core.api import create_api
from core.utils import read_config
from db.pg_core_connect import PgCoreConnect
from models.config_models import WebapiConfig

logger = logging.getLogger(__name__)


async def main():

    con = PgCoreConnect(host='localhost',
                        port=5432,
                        db_name='dev_db',
                        user='app',
                        password='123qwe',
                        application_name='link-cutter')

    await con.connect()
    await con.run_query("START TRANSACTION")    # noqa Q0000
    await con.run_query("insert into links.data(data, dt) values('meme1', $1)",
                        datetime.now(tz=timezone(timedelta(hours=3))))
    await con.run_query("COMMIT")    # noqa Q0000
    # await con.run_query("ROLLBACK")

    await con.run_query('select * from links.data ')


async def start_webserver():

    api = create_api()    # noqa F841
    cfg = WebapiConfig(**read_config().get('webapi'))
    uvicorn.run('api:web_api', port=cfg.port)


if __name__ == '__main__':

    with open(Path.cwd() / 'src/log-config.yml', 'r') as stream:
        cfg_ = yaml.safe_load(stream)
        logging.config.dictConfig(cfg_.get('logging'))

    # # asyncio.run(start_webserver()) # noqa E800

    api = create_api()    # noqa F841 # noqa E800
    cfg = WebapiConfig(**read_config().get('webapi'))    # noqa E800
    uvicorn.run('core.api:web_api', port=cfg.port)    # noqa E800
