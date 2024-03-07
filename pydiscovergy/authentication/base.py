"""Base authentication module for Discovergy API."""

from __future__ import annotations

from abc import ABC, abstractmethod

from httpx import AsyncClient  # noqa: TCH002


# pylint: disable=too-few-public-methods
class BaseAuthentication(ABC):
    """Interface class for authentication classes."""

    @abstractmethod
    async def get_client(
        self,
        email: str,
        password: str,
        timeout: int,
        httpx_client: AsyncClient | None = None,
    ) -> AsyncClient:
        """Return httpx AsyncClient for the pydiscovergy client."""
