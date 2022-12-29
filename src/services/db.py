from core.abstract_source import AbstractSource
from core.db_base import DbBase
from db.pg_core_connect import CustomDbError


class DbService(DbBase):

    def __init__(self, db_source: AbstractSource):
        super().__init__(db_source=db_source)

    @property
    def schema(self):
        return self._db_source.schema

    async def check_db(self) -> bool:
        try:
            self._logger.info('Проверка подключения к БД...')
            _ = await self._execute('select schema_name from information_schema.schemata')
            self._logger.info('подключение к БД успешно')
            return True
        except CustomDbError as e:    # noqa B902
            self._logger.error(e)
            self._logger.info('не удалось подклюиться к БД')
            return False

    async def create_link(self, url_id: str, original_url: str):

        stmt = f'INSERT INTO {self.schema}.links(url_id, original_url) values($1,$2)'
        await self._execute('START TRANSACTION')
        result = await self._execute(stmt, url_id, original_url)
        await self._execute('COMMIT')

        return result

    async def get_original_by_short(self, url_id: str):
        stmt = f'SELECT url_id, original_url, active from {self.schema}.links where url_id=$1'
        return await self._execute(stmt, url_id)

    async def deactivate_link(self, url_id: str):
        stmt = f'UPDATE {self.schema}.links SET active=0 where url_id=$1'
        await self._execute('START TRANSACTION')
        result = await self._execute(stmt, url_id)
        await self._execute('COMMIT')
        return result

    async def add_statistic(self, url_id: str, info: str):
        stmt = f'INSERT INTO {self.schema}.stats(url_id, info) values($1,$2)'
        await self._execute('START TRANSACTION')
        result = await self._execute(stmt, url_id, info)
        await self._execute('COMMIT')

        return result

    async def get_stats_count_by_id(self, url_id: str):
        stmt = f'SELECT count(*) from {self.schema}.stats where url_id=$1 '
        return await self._execute(stmt, url_id)

    async def get_stats_by_url_id(self, url_id: str, offset: int = 0, limit: int = 10):
        stmt = f'SELECT info, happened from {self.schema}.stats where url_id=$1 limit $2 offset $3'
        return await self._execute(stmt, url_id, limit, offset)
