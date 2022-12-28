from typing import Callable, Optional


class QueryContext:

    def __init__(self,
                 stmt: Optional[str] = None,
                 columns: Optional[list] = None,
                 type_converters: Optional[list[Callable]] = None):
        self._stmt = stmt
        self._rows = None if columns is None else []
        self._rows_count = -1
        self._columns = columns
        self._type_converters = [] if type_converters is None else type_converters
        self.error = None

    @property
    def stmt(self):
        return self._stmt

    @property
    def rows(self):
        return self._rows

    @property
    def type_converters(self) -> list[Callable]:
        return self._type_converters

    @property
    def columns(self):
        return self._columns

    @property
    def rows_count(self):
        return self._rows_count

    @type_converters.setter
    def type_converters(self, value: list[Callable]):
        self._type_converters = value

    @columns.setter
    def columns(self, values: list):
        self._columns = values

    @rows.setter
    def rows(self, values: list):
        self._rows = values

    @rows_count.setter
    def rows_count(self, value: int):
        self._rows_count = value
