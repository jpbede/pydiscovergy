from __future__ import annotations

import json
import logging
from urllib.parse import parse_qs

import httpx
from authlib.integrations.httpx_client import AsyncOAuth1Client

from .const import (API_ACCESS_TOKEN, API_AUTHORIZATION, API_BASE,
                    API_CONSUMER_TOKEN, API_REQUEST_TOKEN, DEFAULT_TIMEOUT)
from .error import AccessTokenExpired, HTTPError, InvalidLogin, MissingToken
from .models import AccessToken, ConsumerToken, Meter, Reading, RequestToken


class Discovergy:

    def __init__(self, app_name: str = "pydicovergy",
                 consumer_token: ConsumerToken = None,
                 access_token: AccessToken = None,
                 timeout: int = DEFAULT_TIMEOUT):
        """Initialize the Python Discovergy class."""
        self.app_name = app_name
        self._timeout = timeout
        self.consumer_token = consumer_token
        self.access_token = access_token

    async def _fetch_consumer_token(self) -> ConsumerToken:
        """Fetches consumer token for app name"""
        async with httpx.AsyncClient() as client:
            try:
                consumer_response = await client.post(url=API_CONSUMER_TOKEN,
                                                      data={"client": self.app_name},
                                                      headers={},
                                                      timeout=self._timeout)
                consumer_response.raise_for_status()

                consumer_tokens = json.loads(consumer_response.content.decode("utf-8"))
                self.consumer_token = ConsumerToken(consumer_tokens["key"], consumer_tokens["secret"])
                return self.consumer_token
            except httpx.RequestError as exc:
                raise HTTPError from exc
            except httpx.HTTPStatusError as exc:
                if exc.response.status_code == 400:
                    raise AccessTokenExpired from exc
                else:
                    raise HTTPError from exc

    async def _fetch_request_token(self) -> RequestToken:
        """Fetch request token"""
        async with AsyncOAuth1Client(client_id=self.consumer_token.key,
                                     client_secret=self.consumer_token.secret) as client:
            try:
                oauth_token_response = await client.fetch_request_token(API_REQUEST_TOKEN)
                return RequestToken(oauth_token_response.get('oauth_token'),
                                    oauth_token_response.get('oauth_token_secret'))
            except httpx.RequestError as exc:
                raise HTTPError from exc
            except httpx.HTTPStatusError as exc:
                if exc.response.status_code == 400:
                    raise AccessTokenExpired from exc
                else:
                    raise HTTPError from exc

    async def _authorize_request_token(self, email: str, password: str, request_token: str):
        """Authorize request token for account"""
        async with httpx.AsyncClient() as client:
            try:
                url = API_AUTHORIZATION + "?oauth_token=" + request_token + \
                      "&email=" + email + "&password=" + password
                response = await client.get(url)
                response.raise_for_status()

                parsed_response = parse_qs(response.content.decode('utf-8'))

                verifier = parsed_response["oauth_verifier"][0]
                return verifier
            except httpx.RequestError as exc:
                raise HTTPError from exc
            except httpx.HTTPStatusError as exc:
                if exc.response.status_code == 400:
                    raise InvalidLogin from exc
                else:
                    raise HTTPError from exc

    async def _fetch_access_token(self, request_token, request_token_secret, verifier) -> AccessToken:
        """Fetch access token"""
        async with AsyncOAuth1Client(client_id=self.consumer_token.key,
                                     client_secret=self.consumer_token.secret,
                                     token=request_token,
                                     token_secret=request_token_secret) as client:
            try:
                access_token_response = await client.fetch_access_token(API_ACCESS_TOKEN, verifier)
                return AccessToken(access_token_response.get('oauth_token'),
                                   access_token_response.get('oauth_token_secret'))
            except httpx.RequestError as exc:
                raise HTTPError from exc
            except httpx.HTTPStatusError as exc:
                if exc.response.status_code == 400:
                    raise AccessTokenExpired from exc
                else:
                    raise HTTPError from exc

    async def login(self, email: str, password: str) -> tuple[AccessToken, ConsumerToken]:
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
        verifier = await self._authorize_request_token(email=email,
                                                       password=password,
                                                       request_token=temp_request_token.token)

        # trade the authorized temporarily request token to an access token
        self.access_token = await self._fetch_access_token(request_token=temp_request_token.token,
                                                           request_token_secret=temp_request_token.token_secret,
                                                           verifier=verifier)
        return self.access_token, self.consumer_token

    def _get_oauth_client_params(self):
        """Return parameters for the OAuth1Client"""
        if self.consumer_token is None:
            raise MissingToken("Consumer token is missing")
        elif self.access_token is None:
            raise MissingToken("Access token is missing")

        return {
            "client_id": self.consumer_token.key,
            "client_secret": self.consumer_token.secret,
            "token": self.access_token.token,
            "token_secret": self.access_token.token_secret,
        }

    async def get_meters(self):
        """Get smart meters"""
        async with AsyncOAuth1Client(**self._get_oauth_client_params()) as client:
            try:
                response = await client.get(API_BASE + "/meters")
                response.raise_for_status()

                result = []
                for jsonMeter in json.loads(response.content.decode("utf-8")):
                    result.append(Meter(**jsonMeter))
                return result
            except httpx.RequestError as exc:
                raise HTTPError from exc
            except httpx.HTTPStatusError as exc:
                if exc.response.status_code == 400:
                    raise AccessTokenExpired from exc
                else:
                    raise HTTPError from exc

    async def get_last_reading(self, meter_id):
        """Get last reading for meter"""
        async with AsyncOAuth1Client(**self._get_oauth_client_params()) as client:
            try:
                response = await client.get(API_BASE + "/last_reading?meterId=" + str(meter_id))
                response.raise_for_status()

                return Reading(**json.loads(response.content.decode("utf-8")))
            except httpx.RequestError as exc:
                raise HTTPError from exc
            except httpx.HTTPStatusError as exc:
                if exc.response.status_code == 400:
                    raise AccessTokenExpired from exc
                else:
                    raise HTTPError from exc

    async def get_readings(self, meter_id, starttime: int, endtime: int = 0, resolution: str = "",
                           fields: str = "field_names",
                           disaggregation: bool = False,
                           each: bool = False):
        """Return the measurements for the specified meter in the specified time interval

        each: Return data from the virtual meter itself (false) or all its sub-meters (true). Only applies if meterId refers to a virtual meter

        disaggregation:  Include load disaggregation as pseudo-measurement fields, if available. Only applies if raw resolution is selected

        resolution: Time distance between returned readings. Possible values:
        raw:                1 day
        three_minutes:      10 days
        fifteen_minutes:    31 days
        one_hour:           93 days
        one_day:            10 years
        one_week:	        20 years
        one_month:	        50 years
        one_year:	        100 years

        starttime: as unix time stamp in miliseconds

        endtime: as unix time stamp in miliseconds

        fields: comma separated list of fields (get fields data from get_fields function) or put field_names to get all available values
        """
        fieldvariable = "&field_names" if fields == "field_names" else "&fields=" + str(fields)
        endtimevariable = "" if endtime == 0 else "&to=" + str(int(endtime))
        resolutionvariable = "" if resolution == "" else "&resolution=" + str(resolution)
        disaggregationvariable = "&disaggregation=" + str(disaggregation).lower()
        eachvariable = "&each=" + str(each).lower()

        request = API_BASE + "/readings?meterId=" + str(meter_id) + fieldvariable + "&from=" + str(
            starttime) + endtimevariable + resolutionvariable + disaggregationvariable + eachvariable

        async with AsyncOAuth1Client(**self._get_oauth_client_params()) as client:
            try:
                response = await client.get(request)
                response.raise_for_status()

                result = []
                for jsonReading in json.loads(response.content.decode("utf-8")):
                    result.append(Reading(**jsonReading))
                return result
            except httpx.RequestError as exc:
                raise HTTPError from exc
            except httpx.HTTPStatusError as exc:
                if exc.response.status_code == 400:
                    raise AccessTokenExpired from exc
                else:
                    raise HTTPError from exc

    async def get_field_names(self, meter_id):
        """Return all available measurement field names for the specified meter"""
        async with AsyncOAuth1Client(**self._get_oauth_client_params()) as client:
            try:
                response = await client.get(API_BASE + "/field_names?meterId=" + str(meter_id))
                response.raise_for_status()

                return json.loads(response.content.decode("utf-8"))
            except httpx.RequestError as exc:
                raise HTTPError from exc
            except httpx.HTTPStatusError as exc:
                if exc.response.status_code == 400:
                    raise AccessTokenExpired from exc
                else:
                    raise HTTPError from exc

    async def get_devices_for_meter(self, meter_id):
        """Get devices by meter id"""
        async with AsyncOAuth1Client(**self._get_oauth_client_params()) as client:
            try:
                response = await client.get(API_BASE + "/devices?meterId=" + str(meter_id))
                response.raise_for_status()

                return json.loads(response.content.decode("utf-8"))
            except httpx.RequestError as exc:
                raise HTTPError from exc
            except httpx.HTTPStatusError as exc:
                if exc.response.status_code == 400:
                    raise AccessTokenExpired from exc
                else:
                    raise HTTPError from exc

    async def get_statistics(self, meter_id: str, starttime: int, endtime: int = 0, fields="field_names"):
        """Return various statistics calculated over all measurements for the specified meter in the specified time interval

        field_names: default value which gives out stats for all available fields
        carry out get_fields command to get all available field options for the specific meter
        enter start- and endtime as time in miliseconds"""
        fieldvariable = "&field_names" if fields == "field_names" else "&fields=" + str(fields)
        endtimevariable = "" if endtime == 0 else "&to=" + str(endtime)

        request = API_BASE + "/statistics?meterId=" + str(meter_id) + fieldvariable + "&from=" + str(
            starttime) + endtimevariable

        async with AsyncOAuth1Client(**self._get_oauth_client_params()) as client:
            try:
                response = await client.get(API_BASE + "/field_names?meterId=" + str(meter_id))
                response.raise_for_status()

                return json.loads(response.content.decode("utf-8")), request, response
            except httpx.RequestError as exc:
                raise HTTPError from exc
            except httpx.HTTPStatusError as exc:
                if exc.response.status_code == 400:
                    raise AccessTokenExpired from exc
                else:
                    raise HTTPError from exc
