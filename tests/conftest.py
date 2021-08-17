import pytest
import respx

import pydiscovergy
from pydiscovergy.const import (
    API_ACCESS_TOKEN,
    API_AUTHORIZATION,
    API_CONSUMER_TOKEN,
    API_REQUEST_TOKEN,
)
from pydiscovergy.models import AccessToken, ConsumerToken


@pytest.fixture
def mocked_login():
    with respx.mock(base_url="https://foo.bar", assert_all_called=False) as respx_mock:
        respx_mock.post(API_CONSUMER_TOKEN).respond(
            json={"key": "consumer_token", "secret": "consumer_token_secret"}
        )

        respx_mock.post(API_REQUEST_TOKEN).respond(
            json={
                "oauth_token": "request_token",
                "oauth_token_secret": "request_token_secret",
            }
        )

        respx_mock.get(API_AUTHORIZATION).respond(
            content="oauth_verifier=i-am-a-verifier-string"
        )

        respx_mock.post(API_ACCESS_TOKEN).respond(
            json={
                "oauth_token": "access_token",
                "oauth_token_secret": "access_token_secret",
            }
        )

        yield respx_mock


@pytest.fixture
def discovergy_mock():
    instance = pydiscovergy.Discovergy(
        "pytest",
        consumer_token=ConsumerToken("consumer_token", "consumer_token_secret"),
        access_token=AccessToken("access_token", "access_token_secret"),
    )
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
