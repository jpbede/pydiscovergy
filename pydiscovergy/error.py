"""Exceptions for Discovergy API."""


class DiscovergyError(Exception):
    """Generic error occurred in Discovergy package."""


class DiscovergyClientError(DiscovergyError):
    """Error occurred when there was a client error in Discovergy package."""


class AccessTokenExpired(DiscovergyError):  # noqa: N818
    """Expired access token exception."""


class InvalidLogin(DiscovergyError):  # noqa: N818
    """Invalid login exception."""


class MissingToken(DiscovergyError):  # noqa: N818
    """Token is missing exception."""


class HTTPError(DiscovergyError):
    """HTTP error."""
