"""Discovergy API."""
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from typing import Any

import httpx

from .authentication import BaseAuthentication, BasicAuth, TokenAuth
from .const import API_BASE, DEFAULT_TIMEOUT, Resolution
from .error import (
    AccessTokenExpired,
    DiscovergyClientError,
    DiscovergyError,
    HTTPError,
    InvalidLogin,
)
from .marshmallow import DeviceList, FieldNameList, Statistics
from .models import Meter, Reading, Statistic


@dataclass
class Discovergy:
    """Async client for Discovergy API."""

    email: str
    password: str
    timeout: int = DEFAULT_TIMEOUT
    httpx_client: httpx.AsyncClient | None = None
    authentication: BaseAuthentication = BasicAuth()

    async def _get(self, path: str, params: dict[str, Any] | None = None) -> Any:
        """Execute a GET request against the API."""

        # remove keys with empty values
        if params is not None:
            params = {key: value for (key, value) in params.items() if value != ""}

        # get ready to use client from authentication module
        client = await self.authentication.get_client(
            email=self.email,
            password=self.password,
            timeout=self.timeout,
            httpx_client=self.httpx_client,
        )

        try:
            async with client:
                response = await client.get(url=API_BASE + path, params=params)
                response.raise_for_status()

                decoded = response.content.decode("utf-8")
                if decoded != "":
                    return json.loads(decoded)

                return None
        except httpx.TimeoutException as exception:
            raise DiscovergyClientError(
                "Timeout occurred while connecting to Discovergy."
            ) from exception
        except httpx.RequestError as exception:
            raise DiscovergyClientError(
                "Unexpected error occurred while executing request"
            ) from exception
        except httpx.HTTPStatusError as exception:
            if exception.response.status_code == 401 and isinstance(
                self.authentication, TokenAuth
            ):
                raise AccessTokenExpired from exception

            if exception.response.status_code == 401 and isinstance(
                self.authentication, BasicAuth
            ):
                raise InvalidLogin from exception

            raise HTTPError(
                f"Request failed with HTTP status {exception.response.status_code}: "
                f"{exception.response.content!r}"
            ) from exception
        except json.JSONDecodeError as exception:
            raise DiscovergyError(f"JSON decoding failed: {exception}") from exception

    async def meters(self) -> list[Meter]:
        """Get list of smart meters."""
        response = await self._get("/meters")
        if response is not None:
            return Meter.schema().load(response, many=True)  # type: ignore[attr-defined]
        return []

    async def meter_last_reading(self, meter_id: str) -> Reading:
        """Get last reading for meter"""
        response = await self._get("/last_reading", params={"meterId": meter_id})
        if response is not None:
            return Reading.schema().load(response, partial=True)  # type: ignore[attr-defined]

        return Reading(time=datetime.utcnow(), values={})

    async def meter_readings(
        self,
        meter_id: str,
        start_time: datetime,
        end_time: datetime | None = None,
        resolution: Resolution | None = None,
        field_names: list[str] | None = None,
        disaggregation: bool = False,
        each: bool = False,
    ) -> list[Reading]:
        """Return the measurements for the specified meter in the specified time interval

        start_time: as datetime

        end_time: as datetime

        resolution: Time distance between returned readings.

        field_names: list of fields (get field names with Discovergy.meter_field_names() function)

        disaggregation:  Include load disaggregation as pseudo-measurement fields, if available.
        Only applies if raw resolution is selected

        each: Return data from the virtual meter itself (false) or all its sub-meters (true).
        Only applies if meterId refers to a virtual meter
        """

        params = {
            "meterId": meter_id,
            "from": str(int(start_time.timestamp() * 1000)),
            "to": ("" if end_time is None else str(int(end_time.timestamp() * 1000))),
            "fields": ("" if field_names is None else ",".join(field_names)),
            "resolution": ("" if resolution is None else str(resolution)),
            "disaggregation": str(disaggregation).lower(),
            "each": str(each).lower(),
        }

        response = await self._get("/readings", params)
        if response is not None:
            return Reading.schema().load(response, many=True)  # type: ignore[attr-defined]
        return []

    async def meter_field_names(self, meter_id: str) -> list[str]:
        """Return all available measurement field names for the specified meter."""
        field_names = await self._get("/field_names", params={"meterId": meter_id})
        if field_names is not None:
            return FieldNameList.schema().load({"field_names": field_names}).field_names
        return []

    async def meter_devices(self, meter_id: str) -> list[str]:
        """Return all recognized devices by meter id."""
        devices = await self._get("/devices", params={"meterId": meter_id})
        if devices is not None:
            return DeviceList.schema().load({"devices": devices}).devices
        return []

    async def meter_statistics(
        self,
        meter_id: str,
        start_time: datetime,
        end_time: datetime | None = None,
        field_names: list[str] | None = None,
    ) -> dict[str, Statistic]:
        """Return various statistics calculated over all measurements for the specified meter
         in the specified time interval

        start_time: as datetime

        end_time: as datetime

        field_names: list of fields (get field names with Discovergy.meter_field_names() function)
        """

        params = {
            "meterId": meter_id,
            "from": str(int(start_time.timestamp() * 1000)),
            "to": ("" if end_time is None else str(int(end_time.timestamp() * 1000))),
            "fields": ("" if field_names is None else ",".join(field_names)),
        }

        statistics = await self._get("/statistics", params)
        if statistics is not None:
            return Statistics.schema().load({"statistics": statistics}).statistics
        return {}
