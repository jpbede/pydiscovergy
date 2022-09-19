from __future__ import annotations

import httpx
from httpx import AsyncClient

from pydiscovergy.authentication import BaseAuthentication


class BasicAuth(BaseAuthentication):

    def __init__(self):
        pass

    async def get_client(self, email: str, password: str, httpx_client: AsyncClient = None) -> AsyncClient:
        if not httpx_client:
            httpx_client = AsyncClient()

        httpx_client.auth = httpx.BasicAuth(email, password)
        return httpx_client
