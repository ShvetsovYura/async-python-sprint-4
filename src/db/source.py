from typing import Optional

from db.connect import DbConnect
from models.config_models import DbConfig


class DbSource:

    def __init__(self, db_config: DbConfig):
        self._db_cfg = db_config

        self._connection: Optional[DbConnect] = None

    @property
    def schema(self):
        return self._db_cfg.schema

    async def acquire(self) -> DbConnect:
        if not self._connection:
            self._connection = DbConnect(host=self._db_cfg.host,
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
