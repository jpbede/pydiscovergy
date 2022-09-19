from httpx import AsyncClient


class BaseAuthentication:

    def __init__(self):
        """Interface class for authentication classes"""

    def get_client(self, email: str, password: str, httpx_client: AsyncClient = None) -> AsyncClient:
        pass
