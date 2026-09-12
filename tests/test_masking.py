from copy import deepcopy

from achlens.core import build_record, mask, parse
from achlens.core.layouts import default_layouts


def _record(layout_name: str, **values: object) -> str:
    return build_record(default_layouts()[layout_name], **values)


def _parsed_file() -> object:
    file_header = _record(
        "file_header",
        record_type_code=1,
        priority_code=1,
        immediate_destination="123456789",
        immediate_origin="987654321",
        file_creation_date=260911,
        file_id_modifier="A",
        record_size=94,
        blocking_factor=10,
        format_code=1,
    )
    batch_header = _record(
        "batch_header",
        record_type_code=5,
        service_class_code=200,
        company_name="Company",
        company_identification="1234567890",
        standard_entry_class_code="WEB",
        company_entry_description="PAYROLL",
        effective_entry_date=260911,
        originator_status_code=1,
        originating_dfi_identification=12345678,
        batch_number=1,
    )
    entry = _record(
        "entry_detail_web",
        record_type_code=6,
        transaction_code=22,
        receiving_dfi_identification=12345678,
        check_digit=0,
        dfi_account_number="ACCOUNT123456789",
        amount=1250,
        individual_identification_number="ID-12345678901",
        individual_name="Jane Doe",
        addenda_record_indicator=1,
        trace_number=123456789,
    )
    noc = _record(
        "addenda_98_noc",
        record_type_code=7,
        addenda_type_code=98,
        change_code="C01",
        original_entry_trace_number=123456789012345,
        original_receiving_dfi_identification=12345678,
        corrected_data="CORRECTED-ACCOUNT-123456789",
        trace_number=123456789012345,
    )
    return parse("\n".join([file_header, batch_header, entry, noc]))


def test_masks_sensitive_fields_across_nested_records() -> None:
    entry = mask(_parsed_file()).batches[0].entries[0]

    assert entry.detail.fields["dfi_account_number"].value == "************6789"
    assert (
        entry.detail.fields["individual_identification_number"].value
        == "**********8901"
    )
    assert (
        entry.addenda[0].fields["corrected_data"].value == "***********************6789"
    )


def test_reveal_is_explicit_and_source_is_unchanged() -> None:
    source = _parsed_file()
    before = deepcopy(source)

    masked = mask(source)
    revealed = mask(source, reveal=True)

    assert source == before
    assert masked is not source
    assert (
        revealed.batches[0].entries[0].detail.fields["dfi_account_number"].value
        == "ACCOUNT123456789"
    )


def test_short_values_are_fully_masked_and_non_sensitive_values_preserved() -> None:
    source = _parsed_file()
    source.batches[0].entries[0].detail.fields["dfi_account_number"].value = "123"
    masked = mask(source).batches[0].entries[0].detail

    assert masked.fields["dfi_account_number"].value == "***"
    assert masked.fields["amount"].value == 1250
    assert masked.fields["trace_number"].value == 123456789
    assert masked.fields["individual_name"].value == "Jane Doe"


def test_unknown_layouts_and_fields_do_not_crash() -> None:
    source = _parsed_file()
    source.unparsed.append(source.batches[0].entries[0].detail)
    assert mask(source).unparsed


def test_masks_raw_fields_in_every_record_collection() -> None:
    source = _parsed_file()
    detail = source.batches[0].entries[0].detail
    locations = [
        "header",
        "batch_header",
        "batch_control",
        "file_control",
        "padding",
        "unparsed",
    ]
    source.header = deepcopy(detail)
    source.batches[0].header = deepcopy(detail)
    source.batches[0].control = deepcopy(detail)
    source.control = deepcopy(detail)
    source.padding = [deepcopy(detail)]
    source.unparsed = [deepcopy(detail)]

    masked = mask(source)
    records = [
        masked.header,
        masked.batches[0].header,
        masked.batches[0].control,
        masked.control,
        masked.padding[0],
        masked.unparsed[0],
    ]

    for location, record in zip(locations, records):
        assert record is not None, location
        field = record.fields["dfi_account_number"]
        assert field.value == "************6789", location
        expected_field_raw = "*" * (len(detail.fields["dfi_account_number"].raw) - 4)
        expected_field_raw += detail.fields["dfi_account_number"].raw[-4:]
        assert field.raw == expected_field_raw, location
        original_slice = detail.raw[field.start : field.end]
        expected_slice = "*" * (len(original_slice) - 4) + original_slice[-4:]
        assert record.raw[field.start : field.end] == expected_slice, location
        assert record.raw[0] == "6", location
        assert record.raw[1:2] == "2", location
