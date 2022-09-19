import httpx
import pytest

from pydiscovergy import Discovergy
from pydiscovergy.authentication.token import TokenAuth
from pydiscovergy.const import API_BASE
from pydiscovergy.error import (
    DiscovergyError,
    HTTPError,
    DiscovergyClientError,
    AccessTokenExpired,
    InvalidLogin,
    MissingToken,
)
from pydiscovergy.models import ConsumerToken, Reading, RequestToken


@pytest.mark.asyncio
@pytest.mark.respx(base_url=API_BASE)
async def test__get(respx_mock, discovergy_mock) -> None:
    mock_req = respx_mock.get("/test").respond(json={"key": "value"})

    resp = await discovergy_mock._get("/test")

    assert mock_req.called
    assert resp == {"key": "value"}

    # test if error is raised when there is invalid json
    with pytest.raises(DiscovergyError):
        respx_mock.get("/test").respond(content='{"key": "value"')
        await discovergy_mock._get("/test")

    # check if DiscovergyClientError is raised when there was a client error
    with pytest.raises(DiscovergyClientError):
        respx_mock.get("/test").mock(side_effect=httpx.RequestError)
        await discovergy_mock._get("/test")

    # check if AccessTokenExpired is raised when there was a HTTP status 401
    with pytest.raises(AccessTokenExpired):
        respx_mock.get("/test").respond(status_code=401)
        await discovergy_mock._get("/test")

    # check if HTTPError is raised when there was a HTTP status 500
    with pytest.raises(HTTPError):
        respx_mock.get("/test").respond(status_code=500)
        await discovergy_mock._get("/test")


# @pytest.mark.asyncio
# async def test_login(mocked_login) -> None:
#     ta = TokenAuth()
#     di = Discovergy(app_name="test", email="test@example.org", password="test123abc")
#     (access_token, consumer_token)
#
#     assert access_token.token == "m_access_token"
#     assert access_token.token_secret == "m_access_token_secret"
#     assert consumer_token.key == "m_consumer_token"
#     assert consumer_token.secret == "m_consumer_token_secret"
#
#     # check if login is return with consumer and access token if they are already there
#     (access_token, consumer_token) = await di.login("test@example.org", "test123abc")
#
#     assert access_token.token == "m_access_token"
#     assert access_token.token_secret == "m_access_token_secret"
#     assert consumer_token.key == "m_consumer_token"
#     assert consumer_token.secret == "m_consumer_token_secret"
#     assert (
#         mocked_login["consumer_token"].call_count == 1
#     )  # consumer token call should only executed once


# @pytest.mark.asyncio
# async def test_get_oauth_client_params() -> None:
#     instance = Discovergy("pytest")
#
#     with pytest.raises(MissingToken) as exc:
#         instance._get_oauth_client_params()
#
#         assert exc == "Consumer token is missing"
#
#     instance.consumer_token = ConsumerToken("consumer_token", "consumer_token_secret")
#     with pytest.raises(MissingToken) as exc:
#         instance._get_oauth_client_params()
#
#         assert exc == "Access token is missing"

@pytest.mark.asyncio
@pytest.mark.respx(base_url=API_BASE)
async def test_get_meters(respx_mock, discovergy_mock, meter_json_mock) -> None:
    mock_req = respx_mock.get("/meters").respond(json=meter_json_mock)

    meters = await discovergy_mock.get_meters()

    assert mock_req.called
    assert len(meters) == 1
    assert meters[0].get_meter_id() == "f8d610b7a8cc4e73939fa33b990ded54"


@pytest.mark.asyncio
@pytest.mark.respx(base_url=API_BASE)
async def test_get_last_reading(respx_mock, discovergy_mock) -> None:
    mock_req = respx_mock.get("/last_reading?meterId=f8d610b7a8cc4e73939fa33b990ded54").respond(
        json={
            "time": 1629195646015,
            "values": {
                "power": 685190,
                "power3": 125330,
                "energyOut": 11500000000,
                "power1": 348230,
                "energy": 173123071191000,
                "power2": 211630,
            },
        }
    )

    last_reading = await discovergy_mock.get_last_reading("f8d610b7a8cc4e73939fa33b990ded54")

    assert mock_req.called
    assert isinstance(last_reading, Reading)
    assert len(last_reading.values) > 0
    assert last_reading.time != 0


@pytest.mark.asyncio
@pytest.mark.respx(base_url=API_BASE)
async def test_get_devices_for_meter(respx_mock, discovergy_mock) -> None:
    mock_req = respx_mock.get("/devices?meterId=f8d610b7a8cc4e73939fa33b990ded54").respond(
        json=["DEVICE_1", "DEVICE_2", "DEVICE_3"]
    )

    devices = await discovergy_mock.get_devices_for_meter("f8d610b7a8cc4e73939fa33b990ded54")

    assert mock_req.called
    assert len(devices) == 3
    assert devices == ["DEVICE_1", "DEVICE_2", "DEVICE_3"]
