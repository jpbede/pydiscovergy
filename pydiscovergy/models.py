"""Models for Discovergy API."""
from dataclasses import dataclass, field
from datetime import datetime

from dataclasses_json import CatchAll, Undefined, config, dataclass_json


@dataclass
class ConsumerToken:
    """Represents a consumer token pair."""

    key: str
    secret: str


@dataclass
class RequestToken:
    """Represents a request token pair."""

    token: str
    token_secret: str


@dataclass
class AccessToken(RequestToken):
    """Represents an access token pair."""


@dataclass_json
@dataclass
class Location:
    """Represents a smart meter location."""

    street: str
    street_number: str = field(metadata=config(field_name="streetNumber"))
    city: str
    zip: int
    country: str


@dataclass_json
@dataclass
class Reading:
    """Represents a reading of a smart meter."""

    time: datetime = field(
        metadata=config(
            encoder=lambda dt: int(dt.timestamp() * 1000),
            decoder=lambda ts: datetime.fromtimestamp(ts / 1000),
        )
    )
    values: dict


@dataclass_json(undefined=Undefined.INCLUDE)
@dataclass
class Meter:
    """Represents a smart meter."""

    meter_id: str = field(metadata=config(field_name="meterId"))
    serial_number: str = field(metadata=config(field_name="serialNumber"))
    full_serial_number: str = field(metadata=config(field_name="fullSerialNumber"))
    type: str = field(metadata=config(field_name="type"))
    measurement_type: str = field(metadata=config(field_name="measurementType"))
    load_profile_type: str = field(metadata=config(field_name="loadProfileType"))
    location: Location
    additional: CatchAll
