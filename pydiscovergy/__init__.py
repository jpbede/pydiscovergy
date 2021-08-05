import asyncio
import json
import logging
from urllib.parse import parse_qs

import requests
from requests_oauthlib import OAuth1Session

from .const import (API_ACCESS_TOKEN, API_AUTHORIZATION, API_BASE,
                    API_CONSUMER_TOKEN, API_REQUEST_TOKEN, DEFAULT_TIMEOUT)
from .error import HTTPError, InvalidLogin
from .models import ConsumerToken, Meter, Reading, RequestToken

_LOGGER = logging.getLogger(__name__)


async def _run_in_executor(func, *args):
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, func, *args)


class Discovergy:

    def __init__(self, app_name, email, password,
                 timeout=DEFAULT_TIMEOUT, consumer_token=None):
        """Initialize the Python Discovergy class."""
        self.app_name = app_name
        self.email = email
        self.password = password

        self._timeout = timeout
        self.consumer_token = consumer_token

        self._discovergy_oauth = None

    async def fetch_consumer_token(self) -> ConsumerToken:
        """Fetches consumer token for app name"""
        consumer_response = await _run_in_executor(
            lambda: requests.post(API_CONSUMER_TOKEN, data={"client": self.app_name}, headers={}, timeout=self._timeout)
        )

        if consumer_response.status_code != 200:
            raise HTTPError(consumer_response.content)

        consumer_tokens = json.loads(consumer_response.content.decode("utf-8"))
        self.consumer_token = ConsumerToken(consumer_tokens["key"], consumer_tokens["secret"])

        return self.consumer_token

    async def fetch_request_token(self) -> RequestToken:
        """Fetch request token"""

        request_token_oauth = OAuth1Session(self.consumer_token.key,
                                            client_secret=self.consumer_token.secret,
                                            callback_uri='oob')
        oauth_token_response = await _run_in_executor(request_token_oauth.fetch_request_token, API_REQUEST_TOKEN)

        return RequestToken(oauth_token_response.get('oauth_token'), oauth_token_response.get('oauth_token_secret'))

    async def authorize_request_token(self, request_token):
        """Authorize request token for account"""

        url = API_AUTHORIZATION + "?oauth_token=" + request_token + \
              "&email=" + self.email + "&password=" + self.password
        response = await _run_in_executor(lambda: requests.get(url, headers={}, timeout=self._timeout))

        if response.status_code == 403:
            raise InvalidLogin(response.content)
        elif response.status_code != 200:
            raise HTTPError(response.content)

        parsed_response = parse_qs(response.content.decode('utf-8'))

        verifier = parsed_response["oauth_verifier"][0]
        return verifier

    async def fetch_access_token(self, request_token, request_token_secret, verifier) -> RequestToken:
        """Fetch access token"""

        access_token_oauth = OAuth1Session(self.consumer_token.key,
                                           client_secret=self.consumer_token.secret,
                                           resource_owner_key=request_token,
                                           resource_owner_secret=request_token_secret,
                                           verifier=verifier)
        oauth_tokens = await _run_in_executor(access_token_oauth.fetch_access_token, API_ACCESS_TOKEN)

        return RequestToken(oauth_tokens.get('oauth_token'), oauth_tokens.get('oauth_token_secret'))

    async def login(self, access_token: RequestToken = None) -> RequestToken:
        """Do the auth workflow"""

        # when we already have both token pairs we can already setup a OAuth1 session and skip all other steps
        if access_token is not None and self.consumer_token is not None:
            self._discovergy_oauth = OAuth1Session(self.consumer_token.key,
                                                   client_secret=self.consumer_token.secret,
                                                   resource_owner_key=access_token.token,
                                                   resource_owner_secret=access_token.token_secret)
            return access_token

        # check if we've already a consumer token if not request one
        if self.consumer_token is None:
            await self.fetch_consumer_token()

        request_tokens = await self.fetch_request_token()

        verifier = await self.authorize_request_token(request_tokens.token)

        access_token = await self.fetch_access_token(request_tokens.token, request_tokens.token_secret, verifier)

        # Construct OAuth session with access token
        self._discovergy_oauth = OAuth1Session(self.consumer_token.key,
                                               client_secret=self.consumer_token.secret,
                                               resource_owner_key=access_token.token,
                                               resource_owner_secret=access_token.token_secret)

        return access_token

    async def get_meters(self):
        """Get smart meters"""
        response = await _run_in_executor(self._discovergy_oauth.get, API_BASE + "/meters")

        if response.status_code == 200:
            result = []
            for jsonMeter in json.loads(response.content.decode("utf-8")):
                result.append(Meter(**jsonMeter))
            return result
        else:
            raise HTTPError(response.content)

    async def get_last_reading(self, meter_id):
        """Get last reading for meter"""
        response = await _run_in_executor(self._discovergy_oauth.get, API_BASE + "/last_reading?meterId=" + str(meter_id))

        if response.status_code == 200:
            return Reading(**json.loads(response.content.decode("utf-8")))
        else:
            raise HTTPError(response.content)

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
        response = await _run_in_executor(self._discovergy_oauth.get, request)

        if response.status_code == 200:
            result = []
            for jsonReading in json.loads(response.content.decode("utf-8")):
                result.append(Reading(**jsonReading))

            return result
        else:
            raise HTTPError(response.content)

    async def get_field_names(self, meter_id):
        """Return all available measurement field names for the specified meter"""
        response = await _run_in_executor(self._discovergy_oauth.get, API_BASE + "/field_names?meterId=" + str(meter_id))

        if response.status_code == 200:
            return json.loads(response.content.decode("utf-8"))
        else:
            raise HTTPError(response.content)

    async def get_devices_for_meter(self, meter_id):
        """Get devices by meter id"""
        response = await _run_in_executor(self._discovergy_oauth.get, API_BASE + "/devices?meterId=" + str(meter_id))

        if response.status_code == 200:
            return json.loads(response.content.decode("utf-8"))
        else:
            raise HTTPError(response.content)

    async def get_statistics(self, meter_id: str, starttime: int, endtime: int = 0, fields="field_names"):
        """Return various statistics calculated over all measurements for the specified meter in the specified time interval

        field_names: default value which gives out stats for all available fields
        carry out get_fields command to get all available field options for the specific meter
        enter start- and endtime as time in miliseconds"""
        fieldvariable = "&field_names" if fields == "field_names" else "&fields=" + str(fields)
        endtimevariable = "" if endtime == 0 else "&to=" + str(endtime)

        request = API_BASE + "/statistics?meterId=" + str(meter_id) + fieldvariable + "&from=" + str(starttime) + endtimevariable
        response = await _run_in_executor(self._discovergy_oauth.get, request)

        if response.status_code == 200:
            return json.loads(response.content.decode("utf-8")), request, response
        else:
            raise HTTPError(response.content)