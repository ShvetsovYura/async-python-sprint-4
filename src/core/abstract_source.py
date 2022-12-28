from abc import ABC, abstractmethod

from db.abstract_db_connect import AbstractDbConnect


class AbstractSource(ABC):

    @property
    @abstractmethod
    def schema(self) -> str:
        pass

    @abstractmethod
    async def acquire(self) -> AbstractDbConnect:
        pass

    @abstractmethod
    async def close(self) -> None:
        pass
