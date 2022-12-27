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

    async def connect(self):
        con = DbConnect(host='localhost',
                        port=5432,
                        db_name='dev_db',
                        user='app',
                        password='123qwe',
                        application_name='hoho')

        self.connection = await con.connect()

    async def close(self):
        if self._connection:
            await self._connection.close()
