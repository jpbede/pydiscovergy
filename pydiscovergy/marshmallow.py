"""Module contains classes for de-/serialisation with marshmallow."""
from dataclasses import dataclass, field

from dataclasses_json import DataClassJsonMixin, config
from marshmallow import fields

from pydiscovergy.models import Statistic


@dataclass(frozen=True, slots=True)
class DeviceList(DataClassJsonMixin):
    """Helper class to deserialize device data from API."""

    devices: list[str] = field(metadata=config(mm_field=fields.List(fields.String())))


@dataclass(frozen=True, slots=True)
class FieldNameList(DataClassJsonMixin):
    """Helper class to deserialize field name data from API."""

    field_names: list[str] = field(
        metadata=config(mm_field=fields.List(fields.String()))
    )


@dataclass(frozen=True, slots=True)
class Statistics(DataClassJsonMixin):
    """Helper class to deserialize statistics data from API."""

    statistics: dict[str, Statistic] = field(
        metadata=config(
            mm_field=fields.Dict(
                keys=fields.String(),
                values=fields.Nested(Statistic.schema()),  # type: ignore[attr-defined]
            )
        )
    )
