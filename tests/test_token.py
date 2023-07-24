import httpx
import pytest

from pydiscovergy.authentication import ConsumerToken, RequestToken
from pydiscovergy.const import API_BASE
from pydiscovergy.error import (
    DiscovergyClientError,
    DiscovergyError,
    HTTPError,
    InvalidLogin,
    MissingToken,
)


@pytest.mark.asyncio
@pytest.mark.respx(base_url=API_BASE)
async def test_fetch_consumer_token(respx_mock, tokenauth_mock) -> None:
    mock_req = respx_mock.post("/oauth1/consumer_token").respond(
        json={"key": "key123", "secret": "secret123"}
    )

    consumer_token = await tokenauth_mock._fetch_consumer_token()

    assert mock_req.called
    assert isinstance(consumer_token, ConsumerToken)
    assert consumer_token.key == "key123"

    # test if error is raised when there is invalid json
    with pytest.raises(DiscovergyError):
        respx_mock.post("/oauth1/consumer_token").respond(
            content='{"key": "key123", "secret": "secret123"'
        )
        await tokenauth_mock._fetch_consumer_token()

    # test when httpx.RequestError is raised
    with pytest.raises(DiscovergyClientError):
        mock_req2 = respx_mock.post("/oauth1/consumer_token").mock(
            side_effect=httpx.RequestError
        )
        await tokenauth_mock._fetch_consumer_token()

    assert mock_req2.called

    # test for HTTP non 200 response
    with pytest.raises(HTTPError):
        mock_req3 = respx_mock.post("/oauth1/consumer_token").respond(status_code=401)
        await tokenauth_mock._fetch_consumer_token()

    assert mock_req3.called


@pytest.mark.asyncio
@pytest.mark.respx(base_url=API_BASE)
async def test_fetch_request_token(respx_mock, tokenauth_mock) -> None:
    mock_req = respx_mock.post("/oauth1/request_token").respond(
        json={"oauth_token": "key123", "oauth_token_secret": "secret123"}
    )

    request_token = await tokenauth_mock._fetch_request_token()

    assert mock_req.called
    assert isinstance(request_token, RequestToken)
    assert request_token.token == "key123"

    # test when httpx.RequestError is raised
    with pytest.raises(HTTPError):
        mock_req2 = respx_mock.post("/oauth1/request_token").mock(
            side_effect=httpx.RequestError
        )
        await tokenauth_mock._fetch_request_token()

    assert mock_req2.called

    # test for HTTP non 200 response
    with pytest.raises(HTTPError):
        mock_req3 = respx_mock.post("/oauth1/request_token").respond(status_code=401)
        await tokenauth_mock._fetch_request_token()

    assert mock_req3.called


@pytest.mark.asyncio
@pytest.mark.respx(base_url=API_BASE)
async def test_authorize_request_token(respx_mock, tokenauth_mock) -> None:
    mock_req = respx_mock.get("/oauth1/authorize").respond(
        content="oauth_verifier=i-am-a-verifier-string"
    )

    response = await tokenauth_mock._authorize_request_token(
        "test@example.com", "test123", "request_token"
    )

    assert mock_req.called
    assert response == "i-am-a-verifier-string"

    # test when httpx.RequestError is raised
    with pytest.raises(DiscovergyClientError):
        mock_req2 = respx_mock.get("/oauth1/authorize").mock(
            side_effect=httpx.RequestError
        )
        await tokenauth_mock._authorize_request_token(
            "test@example.com", "test123", "request_token"
        )

    assert mock_req2.called

    # test when there is a 403 Unauthorized
    with pytest.raises(InvalidLogin):
        mock_req3 = respx_mock.get("/oauth1/authorize").respond(status_code=403)
        await tokenauth_mock._authorize_request_token(
            "test@example.com", "test123", "request_token"
        )

    assert mock_req3.called

    # test for HTTP non 200 response
    with pytest.raises(HTTPError):
        mock_req3 = respx_mock.get("/oauth1/authorize").respond(status_code=401)
        await tokenauth_mock._authorize_request_token(
            "test@example.com", "test123", "request_token"
        )

    assert mock_req3.called


@pytest.mark.asyncio
@pytest.mark.respx(base_url=API_BASE)
async def test_fetch_access_token(respx_mock, tokenauth_mock) -> None:
    mock_req = respx_mock.post("/oauth1/access_token").respond(
        json={
            "oauth_token": "access_token",
            "oauth_token_secret": "access_token_secret",
        }
    )

    response = await tokenauth_mock._fetch_access_token(
        "request_token", "request_token_secret", "i-am-a-verifier"
    )

    assert mock_req.called
    assert response.token == "access_token"

    # test for HTTP non 200 response
    with pytest.raises(HTTPError):
        mock_req2 = respx_mock.post("/oauth1/access_token").respond(status_code=401)
        await tokenauth_mock._fetch_access_token(
            "request_token", "request_token_secret", "i-am-a-verifier"
        )

    assert mock_req2.called


@pytest.mark.asyncio
async def test_missing_consumer_token(tokenauth_mock) -> None:
    tokenauth_mock.consumer_token = None

    with pytest.raises(MissingToken):
        tokenauth_mock._get_oauth_client_params()


@pytest.mark.asyncio
async def test_missing_access_token(tokenauth_mock) -> None:
    tokenauth_mock.access_token = None

    with pytest.raises(MissingToken):
        tokenauth_mock._get_oauth_client_params()
