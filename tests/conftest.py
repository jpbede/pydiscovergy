"""Fixtures for tests."""

from collections.abc import Generator

import pytest
import respx

import pydiscovergy
from pydiscovergy.authentication import AccessToken, ConsumerToken, TokenAuth
from pydiscovergy.const import (
    API_ACCESS_TOKEN,
    API_AUTHORIZATION,
    API_CONSUMER_TOKEN,
    API_REQUEST_TOKEN,
)


@pytest.fixture
def mocked_login() -> Generator[respx.MockRouter, None, None]:
    """Mock login."""
    with respx.mock(assert_all_called=False) as respx_mock:
        respx_mock.post(url=API_CONSUMER_TOKEN, name="consumer_token").respond(
            json={"key": "m_consumer_token", "secret": "m_consumer_token_secret"},
        )

        respx_mock.post(API_REQUEST_TOKEN).respond(
            json={
                "oauth_token": "m_request_token",
                "oauth_token_secret": "m_request_token_secret",
            },
        )

        respx_mock.get(API_AUTHORIZATION).respond(
            content="oauth_verifier=m_i-am-a-verifier-string",
        )

        respx_mock.post(API_ACCESS_TOKEN).respond(
            json={
                "oauth_token": "m_access_token",
                "oauth_token_secret": "m_access_token_secret",
            },
        )

        yield respx_mock


@pytest.fixture
def discovergy_mock() -> pydiscovergy.Discovergy:
    """Return a Discovergy instance."""
    return pydiscovergy.Discovergy(
        email="example@example.com",
        password="example",
    )


@pytest.fixture
def discovergy_token_mock() -> pydiscovergy.Discovergy:
    """Return a Discovergy instance with token auth."""
    return pydiscovergy.Discovergy(
        email="example@example.com",
        password="example",
        authentication=TokenAuth(
            consumer_token=ConsumerToken("key123", "secret123"),
            access_token=AccessToken("access_token", "access_token_secret"),
        ),
    )


@pytest.fixture
def tokenauth_mock() -> TokenAuth:
    """Return a TokenAuth instance."""
    return TokenAuth(
        consumer_token=ConsumerToken("key123", "secret123"),
        access_token=AccessToken("access_token", "access_token_secret"),
    )
