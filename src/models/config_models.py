from typing import Any

from core.utils import base64_decode


class DbConfig:

    def __init__(    # noqa: CFQ002
            self,
            dsn: str,
            un: str,
            up: str,
            schema: str,
            pool_size: int = 1,
            statement_cache_size=0):
        self.dsn = dsn
        self.un = base64_decode(un)
        self.up = base64_decode(up)
        self.statement_cache_size = statement_cache_size
        self.schema = schema
        self.pool_size = pool_size


class WebapiCorsConfig:

    def __init__(self, methods: list[str], origins: list[str], headers: list[str],
                 credentials: bool) -> None:
        self.credentials = credentials
        self.methdods = methods
        self.origins = origins
        self.headers = headers


class WebapiConfig:

    def __init__(
        self,
        access_token: str,
        cors: Any,
        port: int = 8080,
        prefix: str = '/api/v1',
    ) -> None:
        self.cors = WebapiCorsConfig(**cors)
        self.port = port
        self.prefix = prefix
        self.access_token = access_token
