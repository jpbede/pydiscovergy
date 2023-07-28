"""Models for Discovergy API."""
from dataclasses import dataclass, field
from datetime import datetime

import pytz
from dataclasses_json import CatchAll, LetterCase, Undefined, config, dataclass_json
from marshmallow import fields


@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclass(frozen=True, slots=True)
class Location:
    """Represents a smart meter location."""

    street: str
    street_number: str
    city: str
    zip: int
    country: str


@dataclass_json
@dataclass(frozen=True, slots=True)
class Reading:
    """Represents a reading of a smart meter."""

    time: datetime = field(metadata=config(mm_field=fields.DateTime("timestamp_ms")))
    values: dict[str, float] = field(
        metadata=config(
            mm_field=fields.Dict(keys=fields.String(), values=fields.Float())
        )
    )

    @property
    def time_with_timezone(self) -> datetime:
        return pytz.timezone("UTC").localize(self.time)


@dataclass_json
@dataclass(frozen=True, slots=True)
class Statistic:
    """Represents a meter statistic entry."""

    count: int
    minimum: float
    maximum: float
    mean: float
    variance: float


@dataclass_json(undefined=Undefined.INCLUDE, letter_case=LetterCase.CAMEL)
@dataclass(frozen=True, slots=True)
class Meter:
    """Represents a smart meter."""

    meter_id: str
    serial_number: str
    full_serial_number: str
    type: str
    measurement_type: str
    load_profile_type: str
    location: Location
    additional: CatchAll
