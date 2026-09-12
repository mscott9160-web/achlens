"""Tests for layout-driven ACH record construction."""

import pytest

from achlens.core import build_record
from achlens.core.layouts import default_layouts


def _required_file_header_fields() -> dict[str, object]:
    return {
        "record_type_code": 1,
        "priority_code": 1,
        "immediate_destination": "123456789",
        "immediate_origin": "987654321",
        "file_creation_date": 260911,
        "file_id_modifier": "A",
        "record_size": 94,
        "blocking_factor": 10,
        "format_code": 1,
    }


def test_build_file_header_formats_numeric_and_alphanumeric_fields() -> None:
    layout = default_layouts()["file_header"]

    record = build_record(
        layout,
        record_type_code=1,
        priority_code=1,
        immediate_destination="123456789",
        immediate_origin="987654321",
        file_creation_date=260911,
        file_id_modifier="a",
        record_size=94,
        blocking_factor=10,
        format_code=1,
        immediate_destination_name="Receiving Bank",
    )

    assert len(record) == 94
    assert record[0:3] == "101"
    assert record[3:13] == "123456789 "
    assert record[13:23] == "987654321 "
    assert record[23:29] == "260911"
    assert record[33] == "a"
    assert record[34:37] == "094"
    assert record[40:63] == "Receiving Bank" + " " * 9


def test_build_entry_record_formats_numeric_and_alphanumeric_fields() -> None:
    layout = default_layouts()["entry_detail_ppd"]

    record = build_record(
        layout,
        record_type_code=6,
        transaction_code=22,
        receiving_dfi_identification=12345678,
        check_digit=0,
        dfi_account_number="ABC123",
        amount=1250,
        individual_name="Jane Doe",
        addenda_record_indicator=0,
        trace_number=123456789,
    )

    assert len(record) == 94
    assert record[0:3] == "622"
    assert record[3:11] == "12345678"
    assert record[12:29] == "ABC123" + " " * 11
    assert record[29:39] == "0000001250"
    assert record[54:76] == "Jane Doe" + " " * 14
    assert record[79:94] == "000000123456789"


def test_alphabetic_fields_are_uppercased() -> None:
    record = build_record(
        default_layouts()["batch_header"],
        record_type_code=5,
        service_class_code=200,
        company_name="Company",
        company_identification="1234567890",
        standard_entry_class_code="ppd",
        company_entry_description="PAYROLL",
        effective_entry_date=260911,
        originator_status_code=1,
        originating_dfi_identification=12345678,
        batch_number=1,
    )

    assert record[50:53] == "PPD"


def test_required_omitted_field_is_rejected_with_layout_and_field() -> None:
    with pytest.raises(
        ValueError,
        match="layout 'file_header' field 'record_type_code' is required",
    ):
        build_record(default_layouts()["file_header"])


def test_optional_numeric_blank_fields_are_space_filled() -> None:
    record = build_record(
        default_layouts()["file_header"],
        record_type_code=1,
        priority_code=1,
        immediate_destination="123456789",
        immediate_origin="987654321",
        file_creation_date=260911,
        file_id_modifier="A",
        record_size=94,
        blocking_factor=10,
        format_code=1,
        file_creation_time=None,
    )

    assert len(record) == 94
    assert record[29:33] == " " * 4

    batch_record = build_record(
        default_layouts()["batch_header"],
        record_type_code=5,
        service_class_code=200,
        company_name="Company",
        company_identification="1234567890",
        standard_entry_class_code="PPD",
        company_entry_description="PAYROLL",
        effective_entry_date=260911,
        settlement_date="",
        originator_status_code=1,
        originating_dfi_identification=12345678,
        batch_number=1,
    )
    assert batch_record[75:78] == " " * 3


def test_required_none_or_blank_field_is_rejected() -> None:
    layout = default_layouts()["file_header"]

    for value in (None, " "):
        with pytest.raises(
            ValueError,
            match="layout 'file_header' field 'record_type_code' is required",
        ):
            build_record(layout, record_type_code=value)


def test_unknown_fields_are_rejected() -> None:
    with pytest.raises(ValueError, match="unknown field.*not_a_field"):
        build_record(default_layouts()["file_header"], not_a_field="value")


@pytest.mark.parametrize(
    ("field", "value"),
    [("record_type_code", "123"), ("immediate_origin_name", "X" * 24)],
)
def test_values_exceeding_field_length_are_rejected(field: str, value: str) -> None:
    fields = _required_file_header_fields()
    fields[field] = value
    with pytest.raises(ValueError, match="exceeds field length"):
        build_record(default_layouts()["file_header"], **fields)


def test_non_digit_numeric_values_are_rejected() -> None:
    fields = _required_file_header_fields()
    fields["priority_code"] = "A1"
    with pytest.raises(ValueError, match="numeric field"):
        build_record(default_layouts()["file_header"], **fields)
