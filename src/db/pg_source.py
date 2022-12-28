from typing import Optional

from core.abstract_source import AbstractSource
from db.abstract_db_connect import AbstractDbConnect
from db.pg_core_connect import PgCoreConnect
from models.config_models import DbConfig


class PgDbSource(AbstractSource):

    def __init__(self, db_config: DbConfig):
        self._db_cfg = db_config

        self._connection: Optional[AbstractDbConnect] = None

    @property
    def schema(self):
        return self._db_cfg.schema

    async def acquire(self) -> AbstractDbConnect:
        if not self._connection:
            self._connection = PgCoreConnect(host=self._db_cfg.host,
                                             port=self._db_cfg.port,
                                             db_name=self._db_cfg.db,
                                             user=self._db_cfg.user,
                                             password=self._db_cfg.password,
                                             application_name='link-cutter')
            await self._connection.connect()

        return self._connection

    async def close(self):
        if self._connection:
            await self._connection.close()
