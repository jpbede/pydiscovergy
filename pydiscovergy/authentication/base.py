"""Base authentication module for Discovergy API."""
from abc import ABC, abstractmethod

from httpx import AsyncClient


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
        """Function that needed to be implemented by authentication modules."""
