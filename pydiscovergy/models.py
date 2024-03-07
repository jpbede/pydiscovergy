"""Models for Discovergy API."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any, Self

from mashumaro.config import BaseConfig
from mashumaro.mixins.orjson import DataClassORJSONMixin
from mashumaro.types import SerializationStrategy
import pytz


class MillisecondTimestampStrategy(SerializationStrategy, use_annotations=True):
    """Serialization strategy for timestamps with milliseconds."""

    def serialize(self, value: datetime) -> float:
        """Serialize a datetime to an timestamp."""
        return value.timestamp() * 1000

    def deserialize(self, value: float) -> datetime:
        """Deserialize an timestamp to a datetime."""
        return datetime.fromtimestamp(value / 1000, tz=UTC)


@dataclass(frozen=True, slots=True)
class Location(DataClassORJSONMixin):
    """Represents a smart meter location."""

    street: str
    street_number: str = field(metadata={"alias": "streetNumber"})
    city: str
    zip: int
    country: str


@dataclass(frozen=True, slots=True)
class Reading(DataClassORJSONMixin):
    """Represents a reading of a smart meter."""

    time: datetime
    values: dict[str, float]

    @property
    def time_with_timezone(self) -> datetime:
        """Return the time with timezone."""
        return pytz.timezone("UTC").localize(self.time)

    # pylint: disable=too-few-public-methods
    class Config(BaseConfig):
        """Configuration for mashumaro."""

        serialization_strategy = {  # noqa: RUF012
            datetime: MillisecondTimestampStrategy(),
        }


@dataclass(frozen=True, slots=True)
class Statistic(DataClassORJSONMixin):
    """Represents a meter statistic entry."""

    count: int
    minimum: float
    maximum: float
    mean: float
    variance: float


@dataclass(frozen=True, slots=True)
class Meter:
    """Represents a smart meter."""

    meter_id: str = field(metadata={"alias": "meterId"})
    serial_number: str = field(metadata={"alias": "serialNumber"})
    full_serial_number: str = field(metadata={"alias": "fullSerialNumber"})
    meter_type: str = field(metadata={"alias": "type"})
    measurement_type: str = field(metadata={"alias": "measurementType"})
    load_profile_type: str = field(metadata={"alias": "loadProfileType"})
    location: Location
    additional: dict[str, Any]

    @classmethod
    def __pre_deserialize__(
        cls: type[Self],
        d: dict[Any, Any],
    ) -> dict[Any, Any]:
        """Move additional fields to a separate dict."""
        non_additional = {
            "meterId",
            "serialNumber",
            "fullSerialNumber",
            "type",
            "measurementType",
            "loadProfileType",
            "location",
        }
        return {
            **d,
            "additional": {k: v for k, v in d.items() if k not in non_additional},
        }


@dataclass(frozen=True, slots=True)
class MetersResponse(DataClassORJSONMixin):
    """Represents a response with all meters."""

    meters: list[Meter]

    @classmethod
    def __pre_deserialize__(
        cls: type[Self],
        d: dict[Any, Any],
    ) -> dict[Any, Any]:
        """Wrap meters in a dict for deserialization."""
        return {"meters": d}
