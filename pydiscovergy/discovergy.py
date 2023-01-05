"""Discovergy API."""
from __future__ import annotations

from dataclasses import dataclass
import json

from httpx import AsyncClient, HTTPStatusError, RequestError

from .authentication import BaseAuthentication, BasicAuth, TokenAuth
from .const import API_BASE, DEFAULT_APP_NAME
from .error import (
    AccessTokenExpired,
    DiscovergyClientError,
    DiscovergyError,
    HTTPError,
    InvalidLogin,
)
from .models import Meter, Reading


@dataclass
class Discovergy:
    """Discovergy API."""

    email: str
    password: str
    app_name: str = DEFAULT_APP_NAME
    httpx_client: AsyncClient = None
    authentication: BaseAuthentication = BasicAuth()

    async def _get(self, path: str, params: dict = None) -> str:
        """Execute a GET request against the API."""
        self.authentication.app_name = self.app_name

        async with await self.authentication.get_client(
            self.email, self.password, self.httpx_client
        ) as client:
            try:
                response = await client.get(API_BASE + path, params=params)
                response.raise_for_status()

                return json.loads(response.content.decode("utf-8"))
            except RequestError as exc:
                raise DiscovergyClientError from exc
            except HTTPStatusError as exc:
                if exc.response.status_code == 401 and isinstance(
                    self.authentication, TokenAuth
                ):
                    raise AccessTokenExpired from exc
                if exc.response.status_code == 401 and isinstance(
                    self.authentication, BasicAuth
                ):
                    raise InvalidLogin from exc
                raise HTTPError(
                    f"Request failed with status {exc.response.status_code}: "
                    f"{exc.response.content}"
                ) from exc
            except json.JSONDecodeError as exc:
                raise DiscovergyError("Decoding failed: {exc}") from exc

    async def meters(self) -> tuple(list[Meter]):
        """Get list of smart meters."""
        response = await self._get("/meters")
        return Meter.schema().load(response, many=True)  # pylint: disable=no-member

    async def meter_last_reading(self, meter_id: str) -> Reading:
        """Get last reading for meter"""
        response = await self._get("/last_reading", params={"meterId": meter_id})
        return Reading.from_dict(response)  # pylint: disable=no-member

    async def meter_readings(
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

        return Reading.schema().load(response, many=True)  # pylint: disable=no-member

    async def meter_field_names(self, meter_id: str) -> list:
        """Return all available measurement field names for the specified meter."""
        return await self._get("/field_names", params={"meterId": meter_id})

    async def meter_devices(self, meter_id: str) -> list:
        """Get devices by meter id."""
        return await self._get("/devices", params={"meterId": meter_id})

    async def meter_statistics(
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
