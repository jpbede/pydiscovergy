"""Discovergy API."""
from __future__ import annotations

import json
from typing import Union
from urllib.parse import parse_qs

import httpx
from authlib.integrations.httpx_client import AsyncOAuth1Client

from .const import (
    API_ACCESS_TOKEN,
    API_AUTHORIZATION,
    API_BASE,
    API_CONSUMER_TOKEN,
    API_REQUEST_TOKEN,
    DEFAULT_TIMEOUT,
)
from .error import (
    AccessTokenExpired,
    DiscovergyError,
    HTTPError,
    InvalidLogin,
    MissingToken,
    DiscovergyClientError,
)
from .models import AccessToken, ConsumerToken, Meter, Reading, RequestToken


class Discovergy:
    """Discovergy API."""

    def __init__(
        self,
        app_name: str = "pydicovergy",
        consumer_token: ConsumerToken = None,
        access_token: AccessToken = None,
        timeout: int = DEFAULT_TIMEOUT,
    ) -> None:
        """Initialize the Python Discovergy class."""
        self.app_name = app_name
        self._timeout = timeout
        self.consumer_token = consumer_token
        self.access_token = access_token

    async def _get(self, path: str) -> dict | list:
        """Execute a GET request against the API."""
        async with AsyncOAuth1Client(**self._get_oauth_client_params()) as client:
            try:
                response = await client.get(API_BASE + path)
                response.raise_for_status()

                return json.loads(response.content.decode("utf-8"))
            except httpx.RequestError as exc:
                raise DiscovergyClientError from exc
            except httpx.HTTPStatusError as exc:
                if exc.response.status_code == 401:
                    raise AccessTokenExpired from exc
                raise HTTPError(
                    f"Request failed with status {exc.response.status_code}: {exc.response.content}"
                ) from exc
            except json.JSONDecodeError as exc:
                raise DiscovergyError("Decoding failed: {exc}") from exc

    async def _fetch_consumer_token(self) -> ConsumerToken:
        """Fetches consumer token for app name"""
        async with httpx.AsyncClient() as client:
            try:
                consumer_response = await client.post(
                    url=API_CONSUMER_TOKEN,
                    data={"client": self.app_name},
                    timeout=self._timeout,
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
    ) -> str:
        """Authorize request token for account"""
        async with httpx.AsyncClient() as client:
            try:
                url = (
                    API_AUTHORIZATION
                    + "?oauth_token="
                    + request_token
                    + "&email="
                    + email
                    + "&password="
                    + password
                )
                response = await client.get(url)
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

    async def login(
        self, email: str, password: str
    ) -> Union[tuple[AccessToken, ConsumerToken], tuple[AccessToken, None]]:
        """Do the auth workflow"""

        # class already initialised with consumer and access token so we don't need to request one
        if self.consumer_token is not None and self.access_token is not None:
            return self.access_token, self.consumer_token

        # no access token and consumer token were supplied so we need to do the auth workflow
        # first fetch a consumer token
        await self._fetch_consumer_token()

        # then fetch a temporarily request token
        temp_request_token = await self._fetch_request_token()

        # authorize the temporarily request token with email and password
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

    async def get_meters(self) -> list[Meter]:
        """Get smart meters"""
        response = await self._get("/meters")

        result = []
        for json_meter in response:
            result.append(Meter(**json_meter))
        return result

    async def get_last_reading(self, meter_id: str) -> Reading:
        """Get last reading for meter"""
        response = await self._get("/last_reading?meterId=" + meter_id)
        return Reading(**response)

    # pylint: disable=too-many-arguments
    async def get_readings(
        self,
        meter_id: str,
        start_time: int,
        end_time: int = 0,
        resolution: str = "",
        fields: list = None,
        disaggregation: bool = False,
        each: bool = False,
    ) -> list[Reading]:
        """Return the measurements for the specified meter in the specified time interval

        each: Return data from the virtual meter itself (false) or all its sub-meters (true).
        Only applies if meterId refers to a virtual meter

        disaggregation:  Include load disaggregation as pseudo-measurement fields, if available.
        Only applies if raw resolution is selected

        resolution: Time distance between returned readings. Possible values:
        raw:                1 day
        three_minutes:      10 days
        fifteen_minutes:    31 days
        one_hour:           93 days
        one_day:            10 years
        one_week:	        20 years
        one_month:	        50 years
        one_year:	        100 years

        start_time: as unix time stamp in miliseconds

        end_time: as unix time stamp in miliseconds

        fields: comma separated list of fields (get field names with get_field_names function)
        or put field_names to get all available values
        """
        response = await self._get(
            "/readings?meterId="
            + meter_id
            + ("&field_names" if fields is None else "&fields=" + ",".join(fields))
            + "&from="
            + str(start_time)
            + ("" if end_time == 0 else "&to=" + str(int(end_time)))
            + ("" if resolution == "" else "&resolution=" + str(resolution))
            + "&disaggregation="
            + str(disaggregation).lower()
            + "&each="
            + str(each).lower()
        )

        result = []
        for json_reading in response:
            result.append(Reading(**json_reading))
        return result

    async def get_field_names(self, meter_id: str) -> list:
        """Return all available measurement field names for the specified meter."""
        return await self._get("/field_names?meterId=" + meter_id)

    async def get_devices_for_meter(self, meter_id: str) -> list:
        """Get devices by meter id."""
        return await self._get("/devices?meterId=" + meter_id)

    async def get_statistics(
        self,
        meter_id: str,
        start_time: int,
        end_time: int = 0,
        fields: list = None,
    ) -> dict | list:
        """Return various statistics calculated over all measurements for the specified meter
         in the specified time interval

        field_names: default value which gives out stats for all available fields
        carry out get_field_names function to get all available field options for the specific meter
        enter start- and end_time as time in miliseconds"""

        request = (
            "/statistics?meterId="
            + str(meter_id)
            + ("&field_names" if fields is None else "&fields=" + ",".join(fields))
            + "&from="
            + str(start_time)
            + ("" if end_time == 0 else "&to=" + str(end_time))
        )

        try:
            return await self._get(request)
        except json.JSONDecodeError as exc:
            raise DiscovergyError("Decoding failed: {exc}") from exc
