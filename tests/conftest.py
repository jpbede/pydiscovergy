import pytest
import respx

import pydiscovergy
from pydiscovergy.authentication.basicauth import BasicAuth
from pydiscovergy.authentication.token import TokenAuth
from pydiscovergy.const import (
    API_ACCESS_TOKEN,
    API_AUTHORIZATION,
    API_CONSUMER_TOKEN,
    API_REQUEST_TOKEN,
)
from pydiscovergy.models import ConsumerToken, AccessToken


@pytest.fixture
def mocked_login():
    with respx.mock(assert_all_called=False) as respx_mock:
        respx_mock.post(url=API_CONSUMER_TOKEN, name="consumer_token").respond(
            json={"key": "m_consumer_token", "secret": "m_consumer_token_secret"}
        )

        respx_mock.post(API_REQUEST_TOKEN).respond(
            json={
                "oauth_token": "m_request_token",
                "oauth_token_secret": "m_request_token_secret",
            }
        )

        respx_mock.get(API_AUTHORIZATION).respond(
            content="oauth_verifier=m_i-am-a-verifier-string"
        )

        respx_mock.post(API_ACCESS_TOKEN).respond(
            json={
                "oauth_token": "m_access_token",
                "oauth_token_secret": "m_access_token_secret",
            }
        )

        yield respx_mock


@pytest.fixture
def discovergy_mock():
    instance = pydiscovergy.Discovergy(
        email="demo@discovergy.com",
        password="demo",
        app_name="pytest",
        authentication=BasicAuth(),
    )
    yield instance


@pytest.fixture
def tokenauth_mock():
    instance = TokenAuth(
        consumer_token=ConsumerToken("key123", "secret123"),
        access_token=AccessToken("access_token", "access_token_secret")
    )
    instance.app_name = "pytest"
    yield instance


@pytest.fixture
def meter_json_mock():
    return [
        {
            "meterId": "f8d610b7a8cc4e73939fa33b990ded54",
            "manufacturerId": "ESY",
            "serialNumber": "123456789",
            "fullSerialNumber": "1ESY123456789",
            "location": {
                "street": "Beispielstr.",
                "streetNumber": "22",
                "zip": "56897",
                "city": "Testhausen",
                "country": "DE",
            },
            "administrationNumber": "DE0001234567800000000000012345678",
            "type": "EASYMETER",
            "measurementType": "ELECTRICITY",
            "loadProfileType": "SLP",
            "scalingFactor": 1,
            "currentScalingFactor": 1,
            "voltageScalingFactor": 1,
            "internalMeters": 1,
            "firstMeasurementTime": 1517569090926,
            "lastMeasurementTime": 1629195318032,
        }
    ]
