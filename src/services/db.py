import logging

from db.source import DbSource


class DbService:

    def __init__(self, db_source: DbSource):
        self._db_source = db_source
        self._logger = logging.getLogger(f'{__name__}.{self.__class__.__name__}')

    @property
    def schema(self):
        return self._db_source.schema

    async def check_db(self) -> bool:
        try:
            self._logger.info('Проверка подключения к БД...')
            _ = await self._execute('select schema_name from information_schema.schemata')
            self._logger.info('подключение к БД успешно')
            return True
        except Exception as e:    # noqa B902
            self._logger.error(e)
            self._logger.info('не удалось подклюиться к БД')
            return False

    async def create_link(self, url_id: str, short_url: str, original_url: str):

        stmt = f'INSERT INTO {self.schema}.links(url_id, short_url, original_url) values($1,$2,$3)'
        await self._execute('START TRANSACTION')
        result = await self._execute(stmt, url_id, short_url, original_url)
        await self._execute('COMMIT')

        return result

    async def get_original_by_short(self, url_id: str):
        stmt = f'SELECT original_url from {self.schema}.links where url_id=$1'
        return await self._execute(stmt, url_id)

    async def _execute(self, sql: str, *args):
        connection_ = await self._db_source.acquire()
        result = await connection_.run_query(sql, *args)
        if result.rows and result.columns:
            keys = [col['name'] for col in result.columns]
            return [dict(zip(keys, row)) for row in result.rows]

        if result.rows_count and not result.columns:
            return result.rows_count
