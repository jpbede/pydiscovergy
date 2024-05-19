"""Discovergy constants."""

from enum import StrEnum

DEFAULT_APP_NAME = "pydicovergy"
DEFAULT_TIMEOUT = 10

API_BASE = "https://api.inexogy.com/public/v1"
API_CONSUMER_TOKEN = API_BASE + "/oauth1/consumer_token"
API_REQUEST_TOKEN = API_BASE + "/oauth1/request_token"
API_AUTHORIZATION = API_BASE + "/oauth1/authorize"
API_ACCESS_TOKEN = API_BASE + "/oauth1/access_token"


class Resolution(StrEnum):
    """Resolutions that can be used for readings."""

    RAW = "raw"
    THREE_MINUTES = "three_minutes"
    FIFTEEN_MINUTES = "fifteen_minutes"
    ONE_HOUR = "one_hour"
    ONE_DAY = "one_day"
    ONE_WEEK = "one_week"
    ONE_MONTH = "one_month"
    ONE_YEAR = "one_year"
