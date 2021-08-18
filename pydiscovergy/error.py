"""Discovergy errors."""


class DiscovergyError(Exception):
    """Generic error occurred in Discovergy package."""


class DiscovergyClientError(DiscovergyError):
    """Error occurred when there was a client error in Discovergy package."""


class AccessTokenExpired(DiscovergyError):
    """Expired access token exception"""


class InvalidLogin(DiscovergyError):
    """Invalid login exception"""


class MissingToken(DiscovergyError):
    """Token is missing exception"""


class HTTPError(DiscovergyError):
    """HTTP error"""
