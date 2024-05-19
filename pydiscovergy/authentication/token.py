"""Authentication module for token auth."""

from __future__ import annotations

from dataclasses import dataclass
import json
from urllib.parse import parse_qs

from authlib.integrations.httpx_client import AsyncOAuth1Client
from httpx import AsyncClient, HTTPStatusError, RequestError

from pydiscovergy.const import (
    API_ACCESS_TOKEN,
    API_AUTHORIZATION,
    API_CONSUMER_TOKEN,
    API_REQUEST_TOKEN,
    DEFAULT_APP_NAME,
)
from pydiscovergy.error import (
    DiscovergyClientError,
    DiscovergyError,
    HTTPError,
    InvalidLogin,
    MissingToken,
)

from .base import BaseAuthentication


@dataclass
class ConsumerToken:
    """Represents a consumer token pair."""

    key: str
    secret: str


@dataclass
class RequestToken:
    """Represents a request token pair."""

    token: str
    token_secret: str


@dataclass
class AccessToken(RequestToken):
    """Represents an access token pair."""


@dataclass
class TokenAuth(BaseAuthentication):
    """Authentication class for token auth."""

    consumer_token: ConsumerToken
    access_token: AccessToken
    app_name: str = DEFAULT_APP_NAME

    async def get_client(
        self,
        email: str,
        password: str,
        timeout: int,
        httpx_client: AsyncClient | None = None,  # noqa: ARG002
    ) -> AsyncOAuth1Client:
        """Return a AsyncOAuth1Client."""
        await self._do_exchange(email, password)
        return AsyncOAuth1Client(**self._get_oauth_client_params(), timeout=timeout)

    async def _do_exchange(
        self,
        email: str,
        password: str,
    ) -> tuple[AccessToken, ConsumerToken] | tuple[AccessToken, None]:
        """Do the auth workflow."""
        # class already initialised with consumer and access token,
        # so we don't need to request one
        if self.consumer_token is not None and self.access_token is not None:
            return self.access_token, self.consumer_token

        # no access token and consumer token were supplied,
        # so we need to do the auth workflow
        # first fetch a consumer token
        await self._fetch_consumer_token()

        # then fetch a temporary request token
        temp_request_token = await self._fetch_request_token()

        # authorize the temporary request token with email and password
        verifier = await self._authorize_request_token(
            email=email,
            password=password,
            request_token=temp_request_token.token,
        )

        # trade the authorized temporarily request token to an access token
        self.access_token = await self._fetch_access_token(
            request_token=temp_request_token.token,
            request_token_secret=temp_request_token.token_secret,
            verifier=verifier,
        )
        return self.access_token, self.consumer_token

    def _get_oauth_client_params(self) -> dict[str, str]:
        """Return parameters for the OAuth1Client."""
        if self.consumer_token is None:
            msg = "Consumer token is missing"
            raise MissingToken(msg)
        if self.access_token is None:
            msg = "Access token is missing"
            raise MissingToken(msg)

        return {
            "client_id": self.consumer_token.key,
            "client_secret": self.consumer_token.secret,
            "token": self.access_token.token,
            "token_secret": self.access_token.token_secret,
        }

    async def _fetch_consumer_token(self) -> ConsumerToken:
        """Fetch a consumer token for app name."""
        async with AsyncClient() as client:
            try:
                consumer_response = await client.post(
                    url=API_CONSUMER_TOKEN,
                    data={"client": self.app_name},
                )
                consumer_response.raise_for_status()

                consumer_tokens = json.loads(consumer_response.content.decode("utf-8"))
                self.consumer_token = ConsumerToken(
                    consumer_tokens["key"],
                    consumer_tokens["secret"],
                )
            except RequestError as exc:
                raise DiscovergyClientError from exc
            except HTTPStatusError as exc:
                msg = f"Status {exc.response.status_code}: {exc.response.content!r}"
                raise HTTPError(
                    msg,
                ) from exc
            except json.JSONDecodeError as exc:
                msg = f"Failed to decode json: {exc}"
                raise DiscovergyError(msg) from exc

            return self.consumer_token

    async def _fetch_request_token(self) -> RequestToken:
        """Fetch request token."""
        async with AsyncOAuth1Client(
            client_id=self.consumer_token.key,
            client_secret=self.consumer_token.secret,
        ) as client:
            try:
                oauth_token_response = await client.fetch_request_token(
                    API_REQUEST_TOKEN,
                )
                return RequestToken(
                    oauth_token_response.get("oauth_token"),
                    oauth_token_response.get("oauth_token_secret"),
                )
            except Exception as exc:
                msg = f"Request failed: {exc}"
                raise HTTPError(msg) from exc

    async def _authorize_request_token(
        self,
        email: str,
        password: str,
        request_token: str,
    ) -> str:
        """Authorize request token for account."""
        async with AsyncClient() as client:
            try:
                params = {
                    "oauth_token": request_token,
                    "email": email,
                    "password": password,
                }
                response = await client.get(API_AUTHORIZATION, params=params)
                response.raise_for_status()

                parsed_response = parse_qs(response.content.decode("utf-8"))

                return parsed_response["oauth_verifier"][0]
            except RequestError as exc:
                raise DiscovergyClientError from exc
            except HTTPStatusError as exc:
                if exc.response.status_code == 403:
                    # the credentials are invalid so raise the correct error
                    raise InvalidLogin from exc
                msg = (
                    f"Request failed with {exc.response.status_code}: "
                    f"{exc.response.content!r}"
                )
                raise HTTPError(
                    msg,
                ) from exc

    async def _fetch_access_token(
        self,
        request_token: str,
        request_token_secret: str,
        verifier: str,
    ) -> AccessToken:
        """Fetch access token."""
        async with AsyncOAuth1Client(
            client_id=self.consumer_token.key,
            client_secret=self.consumer_token.secret,
            token=request_token,
            token_secret=request_token_secret,
        ) as client:
            try:
                access_token_response = await client.fetch_access_token(
                    API_ACCESS_TOKEN,
                    verifier,
                )
                return AccessToken(
                    access_token_response.get("oauth_token"),
                    access_token_response.get("oauth_token_secret"),
                )
            except Exception as exc:
                msg = f"Request failed: {exc}"
                raise HTTPError(msg) from exc
