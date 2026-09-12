"""Typed loading and validation for fixed-width ACH record layouts."""

from dataclasses import dataclass
from functools import lru_cache
from importlib.resources import files
from pathlib import Path
from typing import Any, Mapping, cast

import yaml


@dataclass(frozen=True)
class FieldSpec:
    """A field in a 94-character ACH record layout."""

    name: str
    start: int
    end: int
    length: int
    type: str
    required: bool
    note: str | None = None


@dataclass(frozen=True)
class RecordLayout:
    """The fields describing one fixed-width ACH record type."""

    name: str
    fields: tuple[FieldSpec, ...]


def _required(mapping: Mapping[str, Any], key: str, context: str) -> Any:
    try:
        return mapping[key]
    except KeyError as exc:
        raise ValueError(f"{context} is missing required key {key!r}") from exc


def _field(raw: object, record_name: str, index: int) -> FieldSpec:
    if not isinstance(raw, Mapping):
        raise ValueError(f"record {record_name!r} field {index} must be a mapping")
    context = f"record {record_name!r} field {index}"
    values = cast(Mapping[str, Any], raw)
    field = FieldSpec(
        name=_required(values, "name", context),
        start=_required(values, "start", context),
        end=_required(values, "end", context),
        length=_required(values, "length", context),
        type=_required(values, "type", context),
        required=_required(values, "required", context),
        note=values.get("note"),
    )
    if not isinstance(field.name, str) or not isinstance(field.type, str):
        raise ValueError(f"{context} name and type must be strings")
    if not all(
        isinstance(value, int) and not isinstance(value, bool)
        for value in (field.start, field.end, field.length)
    ):
        raise ValueError(f"{context} positions and length must be integers")
    if not isinstance(field.required, bool):
        raise ValueError(f"{context} required must be a boolean")
    return field


def validate_layout_contiguity(layout: RecordLayout) -> None:
    """Ensure a layout covers every position from 1 through 94 exactly once."""
    expected = 1
    for field in sorted(layout.fields, key=lambda item: item.start):
        if field.length <= 0:
            raise ValueError(
                f"layout {layout.name!r} field {field.name!r} has invalid length"
            )
        if field.end - field.start + 1 != field.length:
            raise ValueError(
                f"layout {layout.name!r} field {field.name!r} has inconsistent length"
            )
        if field.start < 1 or field.end > 94:
            raise ValueError(
                f"layout {layout.name!r} field {field.name!r} is out of range"
            )
        if field.start != expected:
            if field.start < expected:
                detail = "overlap"
            else:
                detail = "gap"
            raise ValueError(
                f"layout {layout.name!r} has {detail} before field {field.name!r}"
            )
        expected = field.end + 1
    if expected != 95:
        raise ValueError(f"layout {layout.name!r} does not end at position 94")


def _parse_layouts(raw: object) -> dict[str, RecordLayout]:
    if not isinstance(raw, Mapping) or not isinstance(raw.get("records"), Mapping):
        raise ValueError("layout YAML must contain a records mapping")
    layouts: dict[str, RecordLayout] = {}
    records = cast(Mapping[str, Any], raw["records"])
    for name, fields in records.items():
        if not isinstance(name, str) or not isinstance(fields, list):
            raise ValueError(
                "each record layout must have a string name and field list"
            )
        layout = RecordLayout(
            name=name,
            fields=tuple(
                _field(field, name, index) for index, field in enumerate(fields)
            ),
        )
        validate_layout_contiguity(layout)
        layouts[name] = layout
    return layouts


def load_layouts(path: str | Path | None = None) -> dict[str, RecordLayout]:
    """Load and validate layouts from *path*, or from the packaged YAML by default."""
    source = (
        Path(path)
        if path is not None
        else Path(files("achlens.core.data").joinpath("ach_layouts.yaml"))
    )
    with source.open(encoding="utf-8") as stream:
        return _parse_layouts(yaml.safe_load(stream))


@lru_cache(maxsize=1)
def default_layouts() -> dict[str, RecordLayout]:
    """Return the cached, validated layouts shipped with achlens."""
    return load_layouts()
