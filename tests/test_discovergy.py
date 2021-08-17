import httpx
import pytest

from pydiscovergy import Discovergy
from pydiscovergy.const import API_BASE
from pydiscovergy.error import HTTPError
from pydiscovergy.models import ConsumerToken, Reading, RequestToken


@pytest.mark.asyncio
async def test_login(mocked_login) -> None:
    di = Discovergy("test")
    (access_token, consumer_token) = await di.login("test@example.org", "test123abc")

    assert access_token.token == "access_token"
    assert access_token.token_secret == "access_token_secret"
    assert consumer_token.key == "consumer_token"
    assert consumer_token.secret == "consumer_token_secret"


@pytest.mark.asyncio
@pytest.mark.respx(base_url=API_BASE)
async def test_fetch_consumer_token(respx_mock) -> None:
    mock_req = respx_mock.post("/oauth1/consumer_token").respond(
        json={"key": "key123", "secret": "secret123"}
    )

    instance = Discovergy("pytest")
    consumer_token = await instance._fetch_consumer_token()

    assert mock_req.called
    assert isinstance(consumer_token, ConsumerToken)
    assert consumer_token.key == "key123"

    # test when httpx.RequestError is raised
    with pytest.raises(HTTPError):
        mock_req2 = respx_mock.post("/oauth1/consumer_token").mock(
            side_effect=httpx.RequestError
        )
        await instance._fetch_consumer_token()

    assert mock_req2.called

    # test for HTTP non 200 response
    with pytest.raises(HTTPError):
        mock_req3 = respx_mock.post("/oauth1/consumer_token").respond(status_code=401)
        await instance._fetch_consumer_token()

    assert mock_req3.called


@pytest.mark.asyncio
@pytest.mark.respx(base_url=API_BASE)
async def test_fetch_request_token(respx_mock, discovergy_mock) -> None:
    mock_req = respx_mock.post("/oauth1/request_token").respond(
        json={"oauth_token": "key123", "oauth_token_secret": "secret123"}
    )

    request_token = await discovergy_mock._fetch_request_token()

    assert mock_req.called
    assert isinstance(request_token, RequestToken)
    assert request_token.token == "key123"

    # test when httpx.RequestError is raised
    with pytest.raises(HTTPError):
        mock_req2 = respx_mock.post("/oauth1/request_token").mock(
            side_effect=httpx.RequestError
        )
        await discovergy_mock._fetch_request_token()

    assert mock_req2.called

    # test for HTTP non 200 response
    with pytest.raises(HTTPError):
        mock_req3 = respx_mock.post("/oauth1/request_token").respond(status_code=401)
        await discovergy_mock._fetch_request_token()

    assert mock_req3.called


@pytest.mark.asyncio
@pytest.mark.respx(base_url=API_BASE)
async def test_get_meters(respx_mock, discovergy_mock, meter_json_mock) -> None:
    mock_req = respx_mock.get("/meters").respond(json=meter_json_mock)

    meters = await discovergy_mock.get_meters()

    assert mock_req.called
    assert len(meters) == 1
    assert meters[0].get_meter_id() == "EASYMETER_123456789"


@pytest.mark.asyncio
@pytest.mark.respx(base_url=API_BASE)
async def test_get_last_reading(respx_mock, discovergy_mock) -> None:
    mock_req = respx_mock.get("/last_reading?meterId=EASYMETER_123456789").respond(
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

    last_reading = await discovergy_mock.get_last_reading("EASYMETER_123456789")

    assert mock_req.called
    assert isinstance(last_reading, Reading)
    assert len(last_reading.values) > 0
    assert last_reading.time != 0
