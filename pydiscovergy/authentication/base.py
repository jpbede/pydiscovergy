"""Base authentication module for Discovergy API."""
from abc import ABC, abstractmethod

from httpx import AsyncClient


class BaseAuthentication(ABC):
    """Interface class for authentication classes."""

    app_name: str

    @abstractmethod
    async def get_client(
        self, email: str, password: str, httpx_client: AsyncClient = None
    ) -> AsyncClient:
        """Function that needed to be implemented by authentication modules."""
        raise Exception("NotImplementedException")
