"""Synthetic ACH fixture builders and mutation helpers.

All records in this module are produced from the packaged layout definitions.
"""

from collections.abc import Mapping

from achlens.core import build_record
from achlens.core.layouts import FieldSpec, default_layouts


def _record(layout_name: str, **fields: object) -> str:
    return build_record(default_layouts()[layout_name], **fields)


def valid_file(*, effective_date: int = 260911) -> str:
    """Return a deterministic, balanced one-batch synthetic ACH file."""
    header = _record(
        "file_header",
        record_type_code=1,
        priority_code=1,
        immediate_destination=" 123456780",
        immediate_origin=" 987654321",
        file_creation_date=effective_date,
        file_id_modifier="A",
        record_size=94,
        blocking_factor=10,
        format_code=1,
        immediate_destination_name="SYNTHETIC BANK",
        immediate_origin_name="ACHLENS TEST",
    )
    batch = _record(
        "batch_header",
        record_type_code=5,
        service_class_code=220,
        company_name="ACHLENS TEST",
        company_identification="9876543210",
        standard_entry_class_code="PPD",
        company_entry_description="PAYROLL",
        effective_entry_date=effective_date,
        originator_status_code=1,
        originating_dfi_identification=12345678,
        batch_number=1,
    )
    entry = _record(
        "entry_detail_ppd",
        record_type_code=6,
        transaction_code=22,
        receiving_dfi_identification=12345678,
        check_digit=0,
        dfi_account_number="TESTACCOUNT",
        amount=100,
        individual_name="TEST PERSON",
        addenda_record_indicator=0,
        trace_number=123456780000001,
    )
    batch_control = _record(
        "batch_control",
        record_type_code=8,
        service_class_code=220,
        entry_addenda_count=1,
        entry_hash=12345678,
        total_debit_entry_dollar_amount=0,
        total_credit_entry_dollar_amount=100,
        company_identification="9876543210",
        originating_dfi_identification=12345678,
        batch_number=1,
    )
    file_control = _record(
        "file_control",
        record_type_code=9,
        batch_count=1,
        block_count=1,
        entry_addenda_count=1,
        entry_hash=12345678,
        total_debit_entry_dollar_amount=0,
        total_credit_entry_dollar_amount=100,
    )
    substantive = [header, batch, entry, batch_control, file_control]
    padding = ["9" * 94 for _ in range(5)]
    return "\n".join(substantive + padding)


def _lines(content: str) -> list[str]:
    return content.splitlines()


def _join(lines: list[str], original: str) -> str:
    ending = "\r\n" if "\r\n" in original else "\n"
    return ending.join(lines)


def set_field(
    content: str,
    line_number: int,
    layout_name: str,
    field_name: str,
    value: object,
) -> str:
    """Replace one field in a generated record using its layout definition."""
    lines = _lines(content)
    if not 1 <= line_number <= len(lines):
        raise IndexError("line_number is outside the fixture")
    layout = default_layouts()[layout_name]
    field = next((item for item in layout.fields if item.name == field_name), None)
    if field is None:
        raise KeyError(field_name)
    formatted = _format_value(field, value)
    line = lines[line_number - 1]
    lines[line_number - 1] = line[: field.start - 1] + formatted + line[field.end :]
    return _join(lines, content)


def _format_value(field: FieldSpec, value: object) -> str:
    text = "" if value is None else str(value)
    if field.type == "N":
        if not text.isdigit():
            raise ValueError(f"numeric field {field.name} must contain only digits")
        text = text.rjust(field.length, "0")
    elif field.type == "A":
        text = text.upper().ljust(field.length)
    else:
        text = text.ljust(field.length)
    if len(text) > field.length:
        raise ValueError(f"value for field {field.name} exceeds field length")
    return text


def delete_line(content: str, line_number: int) -> str:
    lines = _lines(content)
    del lines[line_number - 1]
    return _join(lines, content)


def swap_lines(content: str, first: int, second: int) -> str:
    lines = _lines(content)
    lines[first - 1], lines[second - 1] = lines[second - 1], lines[first - 1]
    return _join(lines, content)


def strip_trailing_spaces(line: str) -> str:
    return line.rstrip(" ")


def drop_padding(content: str) -> str:
    return _join([line for line in _lines(content) if line != "9" * 94], content)


def add_padding(content: str, count: int) -> str:
    if count < 0:
        raise ValueError("count cannot be negative")
    return _join(_lines(content) + ["9" * 94] * count, content)


def inject_non_ascii(content: str, line_number: int = 1, character: str = "\x80") -> str:
    if len(character) != 1 or ord(character) <= 0x7E:
        raise ValueError("character must be one non-ASCII character")
    lines = _lines(content)
    lines[line_number - 1] = character + lines[line_number - 1][1:]
    return _join(lines, content)
