import logging
from typing import Any, TypeVar, Union

from core.abstract_source import AbstractSource

# чета я намутрил с аннотациями, подсвечивается как-то странно в роутерах
DbResponse = TypeVar('DbResponse', list[dict[str, Any]], int)

DbResult = Union[DbResponse, None]


class DbBase:

    def __init__(self, db_source: AbstractSource) -> None:

        self._db_source = db_source
        self._logger = logging.getLogger(f'{__name__}.{self.__class__.__name__}')

    async def _execute(self, sql: str, *args) -> DbResult:
        connection_ = await self._db_source.acquire()
        result = await connection_.run_query(sql, *args)
        if result.rows and result.columns:
            keys = [col['name'] for col in result.columns]
            return [dict(zip(keys, row)) for row in result.rows]

        if result.rows_count and not result.columns:
            return result.rows_count
