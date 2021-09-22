"""Discovergy models."""


class ConsumerToken:  # pylint: disable=too-few-public-methods
    """Represents a consumer token pair."""

    def __init__(self, key: str, secret: str) -> None:
        self.key = key
        self.secret = secret


class RequestToken:  # pylint: disable=too-few-public-methods
    """Represents a request token pair."""

    def __init__(self, token: str, token_secret: str) -> None:
        self.token = token
        self.token_secret = token_secret


class AccessToken(RequestToken):  # pylint: disable=too-few-public-methods
    """Represents a access token pair."""


class Meter:  # pylint: disable=too-few-public-methods
    """Represents a meter."""

    def __init__(
        self, meterId: str, serialNumber: str, measurementType: str, location: dict, **kwargs
    ) -> None:
        self.meter_id = meterId
        self.serial_number = serialNumber
        self.full_serial_number = kwargs.get("fullSerialNumber")
        self.type = kwargs.get("type")
        self.measurement_type = measurementType
        self.load_profile_type = kwargs.get("loadProfileType")
        self.location = Location(**location)
        self.additional = kwargs

    def get_meter_id(self) -> str:
        """Get the unique meter id for subsequent API calls."""
        return self.meter_id


class Location:  # pylint: disable=too-few-public-methods
    """Represents a smart meter location."""

    def __init__(
        self, city: str, street: str, streetNumber: str, country: str, **kwargs
    ) -> None:
        self.city = city
        self.street = street
        self.zip = kwargs.get("zip")
        self.street_number = streetNumber
        self.country = country


class Reading:  # pylint: disable=too-few-public-methods
    """Represents a reading."""

    def __init__(self, time: str, values: dict) -> None:
        self.time = time
        self.values = values
