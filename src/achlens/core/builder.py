"""Build fixed-width ACH records from validated layout definitions."""

from typing import Any

from .layouts import RecordLayout


def _format_field(field_type: str, value: Any, length: int, field_name: str) -> str:
    if field_type == "N":
        if value is None:
            text = "0" * length
        else:
            text = str(value)
            if not text.isdigit():
                raise ValueError(f"numeric field {field_name!r} must contain only digits")
        if len(text) > length:
            raise ValueError(
                f"value for field {field_name!r} exceeds field length {length}"
            )
        return text.rjust(length, "0")

    if field_type in {"AN", "A"}:
        text = "" if value is None else str(value)
        if field_type == "A":
            text = text.upper()
        if len(text) > length:
            raise ValueError(
                f"value for field {field_name!r} exceeds field length {length}"
            )
        return text.ljust(length, " ")

    raise ValueError(f"unsupported field type {field_type!r} for field {field_name!r}")


def build_record(layout: RecordLayout, **fields: Any) -> str:
    """Build one 94-character record using the fields in *layout*.

    Numeric fields are zero-filled on the left; alphanumeric and alphabetic
    fields are space-filled on the right. Required fields must be provided with
    a non-blank value; optional omitted or blank fields are space-filled across
    their width. Alphabetic values are uppercased according to the layout type
    semantics.
    """
    field_specs = {field.name: field for field in layout.fields}
    unknown = set(fields) - field_specs.keys()
    if unknown:
        names = ", ".join(sorted(unknown))
        raise ValueError(f"unknown field(s) for layout {layout.name!r}: {names}")

    formatted_fields = []
    for field in layout.fields:
        value = fields.get(field.name)
        is_blank = value is None or (isinstance(value, str) and not value.strip())
        if is_blank:
            if field.required:
                raise ValueError(
                    f"layout {layout.name!r} field {field.name!r} is required"
                )
            formatted_fields.append(" " * field.length)
            continue
        formatted_fields.append(
            _format_field(field.type, value, field.length, field.name)
        )
    record = "".join(formatted_fields)
    if len(record) != 94:
        raise AssertionError(
            f"layout {layout.name!r} produced {len(record)} characters, expected 94"
        )
    return record