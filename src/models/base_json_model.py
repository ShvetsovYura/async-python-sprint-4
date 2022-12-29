import orjson
from pydantic.main import BaseModel


def orjson_dumps(value, *, default):
    return orjson.dumps(value, default=default).decode()


class BaseOrjsonModel(BaseModel):

    class Config:
        json_loads = orjson.loads
        json_dumps = orjson_dumps
