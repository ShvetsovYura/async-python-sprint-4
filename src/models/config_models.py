from dataclasses import dataclass
from typing import Any


@dataclass
class DbConfig:
    host: str
    port: int
    db: str
    schema: str
    user: str
    password: str


class WebapiCorsConfig:

    def __init__(self, methods: list[str], origins: list[str], headers: list[str],
                 credentials: bool) -> None:
        self.credentials = credentials
        self.methods = methods
        self.origins = origins
        self.headers = headers


class WebapiConfig:

    def __init__(
        self,
        cors: Any,
        port: int = 8080,
        prefix: str = '/api/v1',
    ) -> None:
        self.cors = WebapiCorsConfig(**cors)
        self.port = port
        self.prefix = prefix
