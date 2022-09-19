"""Discovergy API."""
from __future__ import annotations

import json

import httpx
from httpx import AsyncClient

from .authentication import BaseAuthentication
from .const import (
    API_BASE,
)
from .error import (
    AccessTokenExpired,
    DiscovergyError,
    HTTPError,
    DiscovergyClientError,
)
from .models import Meter, Reading


class Discovergy:
    """Discovergy API."""

    def __init__(
            self,
            email: str,
            password: str,
            authentication: BaseAuthentication,
            app_name: str = "pydicovergy",
            httpx_client: AsyncClient = None,
    ) -> None:
        """Initialize the Python Discovergy class."""
        self.authentication = authentication
        self.authentication.app_name = app_name

        self.email = email
        self.password = password
        self.app_name = app_name
        self.httpx_client = httpx_client

    async def _get(self, path: str, params: dict = None) -> dict | list:
        """Execute a GET request against the API."""

        async with await self.authentication.get_client(self.email, self.password, self.httpx_client) as client:
            try:
                response = await client.get(API_BASE + path, params=params)
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

    async def get_meters(self) -> list[Meter]:
        """Get smart meters"""
        response = await self._get("/meters")

        result = []
        for json_meter in response:
            result.append(Meter(**json_meter))
        return result

    async def get_last_reading(self, meter_id: str) -> Reading:
        """Get last reading for meter"""
        response = await self._get("/last_reading", params={"meterId": meter_id})
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
        return await self._get("/field_names", params={"meterId": meter_id})

    async def get_devices_for_meter(self, meter_id: str) -> list:
        """Get devices by meter id."""
        return await self._get("/devices", params={"meterId": meter_id})

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
