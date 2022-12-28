from typing import Callable

from fastapi import HTTPException, Request, status


class SubnetCheckMiddleware:

    def __init__(self, subnets: list[str]) -> None:
        self._subnets = subnets

    async def __call__(self, request: Request, call_next: Callable):
        if request.client:
            for subnet_ in self._subnets:
                if request.client.host in subnet_:
                    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                                        detail='Запрещено для этой подсети')

        return await call_next(request)
