"""Authentication module for basic auth."""

from __future__ import annotations

from httpx import AsyncClient, BasicAuth as HttpxBasicAuth

from .base import BaseAuthentication


# pylint: disable=too-few-public-methods
class BasicAuth(BaseAuthentication):
    """Authentication module for basic auth."""

    async def get_client(
        self,
        email: str,
        password: str,
        timeout: int,
        httpx_client: AsyncClient | None = None,
    ) -> AsyncClient:
        """Return a httpx client with basic authentication."""
        if not httpx_client:
            httpx_client = AsyncClient(timeout=timeout)

        httpx_client.auth = HttpxBasicAuth(email, password)
        return httpx_client
