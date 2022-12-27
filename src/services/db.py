import logging

from db.source import DbSource


class DbService:

    def __init__(self, db_source: DbSource):
        self._db_source = db_source
        self._logger = logging.getLogger(f'{__name__}.{self.__class__.__name__}')

    async def check_db(self) -> bool:
        try:
            self._logger.info('Проверка подключения к БД...')
            _ = await self._fetch_all('select schema_name from information_schema.schemata')
            self._logger.info('подключение к БД успешно')
            return True
        except Exception as e:    # noqa B902
            self._logger.error(e)
            self._logger.info('не удалось подклюиться к БД')
            return False

    async def _fetch_all(self, sql: str, *args) -> list:
        connection_ = await self._db_source.acquire()
        context = await connection_.run_query(sql, *args)
        if context.rows:
            return context.rows

        return []
