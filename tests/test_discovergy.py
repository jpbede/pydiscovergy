"""Tests for the Discovergy API client."""

import datetime

import httpx
import pytest
from pytest_httpx import HTTPXMock
from respx import MockRouter

from pydiscovergy import Discovergy
from pydiscovergy.const import API_BASE
from pydiscovergy.error import (
    AccessTokenExpired,
    DiscovergyClientError,
    HTTPError,
    InvalidLogin,
)
from pydiscovergy.models import Reading, Statistic
from tests import load_fixture


@pytest.mark.usefixtures("respx_mock")
@pytest.mark.respx(base_url=API_BASE)
async def test_get_timeout(
    discovergy_mock: Discovergy,
    httpx_mock: HTTPXMock,
) -> None:
    """Test if a error is raised when there was a timeout."""
    httpx_mock.add_exception(httpx.ReadTimeout("Unable to read within timeout"))

    # test if DiscovergyClientError is raised when there was a timeout
    with pytest.raises(DiscovergyClientError):
        await discovergy_mock._get("/test")


@pytest.mark.respx(base_url=API_BASE)
async def test_token_auth_expired(
    respx_mock: MockRouter,
    discovergy_token_mock: Discovergy,
) -> None:
    """Test if a error is raised when the access token is expired."""
    respx_mock.get("/test").respond(json={"key": "value"})

    # check if AccessTokenExpired is raised when there was an HTTP status 401
    with pytest.raises(AccessTokenExpired):
        respx_mock.get("/test").respond(status_code=401)
        await discovergy_token_mock._get("/test")


@pytest.mark.respx(base_url=API_BASE)
async def test__get(respx_mock: MockRouter, discovergy_mock: Discovergy) -> None:
    """Test if a request is made and the response is returned."""
    mock_req = respx_mock.get("/test").respond(json={"key": "value"})

    resp = await discovergy_mock._get("/test")

    assert mock_req.called
    assert resp == '{"key":"value"}'

    # check if DiscovergyClientError is raised when there was a client error
    with pytest.raises(DiscovergyClientError):
        respx_mock.get("/test").mock(side_effect=httpx.RequestError)
        await discovergy_mock._get("/test")

    # check if InvalidLogin is raised when there was an HTTP status 401
    with pytest.raises(InvalidLogin):
        respx_mock.get("/test").respond(status_code=401)
        await discovergy_mock._get("/test")

    # check if HTTPError is raised when there was an HTTP status 500
    with pytest.raises(HTTPError):
        respx_mock.get("/test").respond(status_code=500)
        await discovergy_mock._get("/test")


@pytest.mark.respx(base_url=API_BASE)
async def test_meters(respx_mock: MockRouter, discovergy_mock: Discovergy) -> None:
    """Test if a list of meters is returned."""
    mock_req = respx_mock.get("/meters").respond(text=load_fixture("meters.json"))

    meters = await discovergy_mock.meters()

    assert mock_req.called
    assert len(meters) == 1
    assert meters[0].meter_id == "f8d610b7a8cc4e73939fa33b990ded54"


@pytest.mark.respx(base_url=API_BASE)
async def test_meter_last_reading(
    respx_mock: MockRouter, discovergy_mock: Discovergy
) -> None:
    """Test if the last reading is returned."""
    mock_req = respx_mock.get(
        "/last_reading",
        params={"meterId": "f8d610b7a8cc4e73939fa33b990ded54"},
    ).respond(text=load_fixture("last_reading.json"))

    last_reading = await discovergy_mock.meter_last_reading(
        meter_id="f8d610b7a8cc4e73939fa33b990ded54",
    )

    assert mock_req.called
    assert isinstance(last_reading, Reading)
    assert len(last_reading.values) > 0
    assert last_reading.time != 0


@pytest.mark.respx(base_url=API_BASE)
async def test_meter_last_reading_empty(
    respx_mock: MockRouter,
    discovergy_mock: Discovergy,
) -> None:
    """Test if the last reading is returned."""
    mock_req = respx_mock.get(
        "/last_reading",
        params={"meterId": "f8d610b7a8cc4e73939fa33b990ded54"},
    ).respond(text="")

    last_reading = await discovergy_mock.meter_last_reading(
        meter_id="f8d610b7a8cc4e73939fa33b990ded54",
    )

    assert mock_req.called
    assert isinstance(last_reading, Reading)


@pytest.mark.respx(base_url=API_BASE)
async def test_meter_devices(
    respx_mock: MockRouter, discovergy_mock: Discovergy
) -> None:
    """Test if a list of devices is returned."""
    mock_req = respx_mock.get(
        "/devices",
        params={"meterId": "f8d610b7a8cc4e73939fa33b990ded54"},
    ).respond(text=load_fixture("devices.json"))

    devices = await discovergy_mock.meter_devices(
        meter_id="f8d610b7a8cc4e73939fa33b990ded54"
    )

    assert mock_req.called
    assert len(devices) == 3
    assert devices == ["DEVICE_1", "DEVICE_2", "DEVICE_3"]
    assert isinstance(devices, list)


@pytest.mark.respx(base_url=API_BASE)
async def test_meter_devices_empty(
    respx_mock: MockRouter, discovergy_mock: Discovergy
) -> None:
    """Test if a list of devices is returned."""
    mock_req = respx_mock.get(
        "/devices",
        params={"meterId": "f8d610b7a8cc4e73939fa33b990ded54"},
    ).respond(text="")

    devices = await discovergy_mock.meter_devices(
        meter_id="f8d610b7a8cc4e73939fa33b990ded54"
    )

    assert mock_req.called
    assert len(devices) == 0
    assert devices == []
    assert isinstance(devices, list)


@pytest.mark.respx(base_url=API_BASE)
async def test_meter_readings(
    respx_mock: MockRouter, discovergy_mock: Discovergy
) -> None:
    """Test if a list of readings is returned."""
    params = {
        "meterId": "f8d610b7a8cc4e73939fa33b990ded54",
        "from": "1673004274648",
        "disaggregation": "false",
        "each": "false",
    }

    mock_req = respx_mock.get("/readings", params=params).respond(
        text=load_fixture("readings.json"),
    )

    readings = await discovergy_mock.meter_readings(
        meter_id="f8d610b7a8cc4e73939fa33b990ded54",
        start_time=datetime.datetime.fromtimestamp(1673004274648 / 1000, datetime.UTC),
    )

    assert mock_req.called == 1
    assert len(readings) == 3
    assert isinstance(readings, list)
    assert isinstance(readings[0], Reading)


@pytest.mark.respx(base_url=API_BASE)
async def test_meter_field_names(
    respx_mock: MockRouter, discovergy_mock: Discovergy
) -> None:
    """Test if a list of field names is returned."""
    params = {
        "meterId": "f8d610b7a8cc4e73939fa33b990ded54",
    }

    mock_req = respx_mock.get("/field_names", params=params).respond(
        text=load_fixture("field_names.json"),
    )

    field_names = await discovergy_mock.meter_field_names(
        meter_id="f8d610b7a8cc4e73939fa33b990ded54",
    )

    assert mock_req.called == 1
    assert len(field_names) == 2
    assert isinstance(field_names, list)


@pytest.mark.respx(base_url=API_BASE)
async def test_meter_statistics(
    respx_mock: MockRouter, discovergy_mock: Discovergy
) -> None:
    """Test if a list of statistics is returned."""
    params = {
        "meterId": "f8d610b7a8cc4e73939fa33b990ded54",
        "from": "1673004274648",
    }

    mock_req = respx_mock.get("/statistics", params=params).respond(
        text=load_fixture("statistics.json"),
    )

    statistics = await discovergy_mock.meter_statistics(
        meter_id="f8d610b7a8cc4e73939fa33b990ded54",
        start_time=datetime.datetime.fromtimestamp(1673004274648 / 1000, datetime.UTC),
    )

    assert mock_req.called == 1
    assert len(statistics) == 2
    assert isinstance(statistics, dict)
    assert "volume" in statistics
    assert isinstance(statistics["volume"], Statistic)
