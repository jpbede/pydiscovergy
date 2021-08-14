class AccessTokenExpired(Exception):
    """Expired access token exception"""


class InvalidLogin(Exception):
    """Invalid login exception"""


class MissingToken(Exception):
    """Token is missing exception"""


class HTTPError(Exception):
    """HTTP error"""
