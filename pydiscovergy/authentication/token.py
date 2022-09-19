from __future__ import annotations

import json
from typing import Union

import httpx
from authlib.integrations.httpx_client import AsyncOAuth1Client
from httpx import AsyncClient

from pydiscovergy.authentication import BaseAuthentication
from pydiscovergy.const import API_CONSUMER_TOKEN, API_REQUEST_TOKEN, API_AUTHORIZATION, API_ACCESS_TOKEN, API_BASE
from pydiscovergy.error import DiscovergyClientError, HTTPError, DiscovergyError, InvalidLogin, AccessTokenExpired, \
    MissingToken
from pydiscovergy.models import ConsumerToken, RequestToken, AccessToken
from urllib.parse import parse_qs


class TokenAuth(BaseAuthentication):

    def __init__(self,
                 consumer_token: ConsumerToken = None,
                 access_token: AccessToken = None):
        """"""
        self.consumer_token = consumer_token
        self.access_token = access_token

    async def get_client(self, email: str, password: str, httpx_client: AsyncClient = None) -> AsyncOAuth1Client:
        await self._do_exchange(email, password)
        return AsyncOAuth1Client(**self._get_oauth_client_params())

    async def _do_exchange(
            self, email: str, password: str
    ) -> Union[tuple[AccessToken, ConsumerToken], tuple[AccessToken, None]]:
        """Do the auth workflow"""

        # class already initialised with consumer and access token so we don't need to request one
        if self.consumer_token is not None and self.access_token is not None:
            return self.access_token, self.consumer_token

        # no access token and consumer token were supplied so we need to do the auth workflow
        # first fetch a consumer token
        await self._fetch_consumer_token()

        # then fetch a temporary request token
        temp_request_token = await self._fetch_request_token()

        # authorize the temporary request token with email and password
        verifier = await self._authorize_request_token(
            email=email, password=password, request_token=temp_request_token.token
        )

        # trade the authorized temporarily request token to an access token
        self.access_token = await self._fetch_access_token(
            request_token=temp_request_token.token,
            request_token_secret=temp_request_token.token_secret,
            verifier=verifier,
        )
        return self.access_token, self.consumer_token

    def _get_oauth_client_params(self) -> dict:
        """Return parameters for the OAuth1Client"""
        if self.consumer_token is None:
            raise MissingToken("Consumer token is missing")
        if self.access_token is None:
            raise MissingToken("Access token is missing")

        return {
            "client_id": self.consumer_token.key,
            "client_secret": self.consumer_token.secret,
            "token": self.access_token.token,
            "token_secret": self.access_token.token_secret,
        }

    async def _fetch_consumer_token(self) -> ConsumerToken:
        """Fetches consumer token for app name"""
        async with httpx.AsyncClient() as client:
            try:
                consumer_response = await client.post(
                    url=API_CONSUMER_TOKEN,
                    data={"client": self.app_name},
                )
                consumer_response.raise_for_status()

                consumer_tokens = json.loads(consumer_response.content.decode("utf-8"))
                self.consumer_token = ConsumerToken(
                    consumer_tokens["key"], consumer_tokens["secret"]
                )
                return self.consumer_token
            except httpx.RequestError as exc:
                raise DiscovergyClientError from exc
            except httpx.HTTPStatusError as exc:
                raise HTTPError(
                    f"Status {exc.response.status_code}: {exc.response.content}"
                ) from exc
            except json.JSONDecodeError as exc:
                raise DiscovergyError(f"Failed to decode json: {exc}") from exc

    async def _fetch_request_token(self) -> RequestToken:
        """Fetch request token"""
        async with AsyncOAuth1Client(
                client_id=self.consumer_token.key, client_secret=self.consumer_token.secret
        ) as client:
            try:
                oauth_token_response = await client.fetch_request_token(
                    API_REQUEST_TOKEN
                )
                return RequestToken(
                    oauth_token_response.get("oauth_token"),
                    oauth_token_response.get("oauth_token_secret"),
                )
            except Exception as exc:
                raise HTTPError(f"Request failed: {exc}") from exc

    async def _authorize_request_token(
            self, email: str, password: str, request_token: str
    ) -> str:  # pylint: disable=no-self-use
        """Authorize request token for account"""
        async with httpx.AsyncClient() as client:
            try:
                params = {
                    "oauth_token": request_token,
                    "email": email,
                    "password": password,
                }
                response = await client.get(API_AUTHORIZATION, params=params)
                response.raise_for_status()

                parsed_response = parse_qs(response.content.decode("utf-8"))

                verifier = parsed_response["oauth_verifier"][0]
                return verifier
            except httpx.RequestError as exc:
                raise DiscovergyClientError from exc
            except httpx.HTTPStatusError as exc:
                if exc.response.status_code == 403:
                    # the credentials are invaild so raise the correct error
                    raise InvalidLogin from exc
                raise HTTPError(
                    f"Request failed with {exc.response.status_code}: {exc.response.content}"
                ) from exc

    async def _fetch_access_token(
            self, request_token, request_token_secret, verifier
    ) -> AccessToken:
        """Fetch access token"""
        async with AsyncOAuth1Client(
                client_id=self.consumer_token.key,
                client_secret=self.consumer_token.secret,
                token=request_token,
                token_secret=request_token_secret,
        ) as client:
            try:
                access_token_response = await client.fetch_access_token(
                    API_ACCESS_TOKEN, verifier
                )
                return AccessToken(
                    access_token_response.get("oauth_token"),
                    access_token_response.get("oauth_token_secret"),
                )
            except Exception as exc:
                raise HTTPError(f"Request failed: {exc}") from exc
