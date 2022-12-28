from abc import ABC, abstractmethod

from db.query_context import QueryContext


class AbstractDbConnect(ABC):

    @abstractmethod
    async def connect(self):
        pass

    @abstractmethod
    async def run_query(self, stmt: str, *params) -> QueryContext:
        pass

    @abstractmethod
    async def run_simple_query(self, stmt: str) -> QueryContext:
        pass

    @abstractmethod
    async def run_query_with_params(self, stmt: str, vals: tuple = (),
                                    oids: tuple = ()) -> QueryContext:
        pass

    @abstractmethod
    async def close(self) -> None:
        pass
