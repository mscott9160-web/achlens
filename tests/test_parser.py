"""Focused tests for tolerant, layout-driven ACH parsing."""

from achlens.core import build_record, parse
from achlens.core.layouts import default_layouts


def _file_header() -> str:
    return build_record(
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
    )


def _batch_header(sec: str) -> str:
    return build_record(
        default_layouts()["batch_header"],
        record_type_code=5,
        service_class_code=200,
        company_name="Company",
        company_identification="1234567890",
        standard_entry_class_code=sec,
        company_entry_description="PAYROLL",
        effective_entry_date=260911,
        originator_status_code=1,
        originating_dfi_identification=12345678,
        batch_number=1,
    )


def _entry(layout_name: str, indicator: int = 1) -> str:
    fields = dict(
        record_type_code=6,
        transaction_code=22,
        receiving_dfi_identification=12345678,
        check_digit=0,
        dfi_account_number="ABC123",
        amount=1250,
        addenda_record_indicator=indicator,
        trace_number=123456789,
    )
    fields["receiving_company_name" if layout_name == "entry_detail_ccd" else "individual_name"] = "Jane Doe"
    return build_record(default_layouts()[layout_name], **fields)


def _addenda() -> str:
    return build_record(
        default_layouts()["addenda_05"],
        record_type_code=7,
        addenda_type_code=5,
        payment_related_information="invoice 42",
        addenda_sequence_number=1,
        entry_detail_sequence_number=3456789,
    )


def _controls() -> tuple[str, str]:
    batch_control = build_record(
        default_layouts()["batch_control"],
        record_type_code=8,
        service_class_code=200,
        entry_addenda_count=2,
        entry_hash=12345678,
        total_debit_entry_dollar_amount=0,
        total_credit_entry_dollar_amount=1250,
        company_identification="1234567890",
        message_authentication_code="",
        originating_dfi_identification=12345678,
        batch_number=1,
    )
    file_control = build_record(
        default_layouts()["file_control"],
        record_type_code=9,
        batch_count=1,
        block_count=1,
        entry_addenda_count=2,
        entry_hash=12345678,
        total_debit_entry_dollar_amount=0,
        total_credit_entry_dollar_amount=1250,
    )
    return batch_control, file_control


def test_parser_decodes_fields_selects_sec_layout_and_attaches_addenda() -> None:
    batch_control, file_control = _controls()
    text = "\n".join(
        [_file_header(), _batch_header("WEB"), _entry("entry_detail_web"), _addenda(), batch_control, file_control, "9" * 94]
    ) + "\n"

    result = parse(text)

    assert result.line_count == 7
    assert result.line_ending == "LF"
    assert result.header is not None and result.header.line_number == 1
    assert result.batches[0].header is not None
    entry = result.batches[0].entries[0]
    assert entry.detail.layout == "entry_detail_web"
    assert entry.detail.fields["amount"].raw == "0000001250"
    assert entry.detail.fields["amount"].value == 1250
    assert entry.addenda[0].layout == "addenda_05"
    assert entry.addenda[0].line_number == 4
    assert result.control is not None and result.control.line_number == 6
    assert [record.line_number for record in result.padding] == [7]
    assert entry.detail.raw.endswith("\n")


def test_parser_uses_ccd_receiving_company_name_fixture() -> None:
    result = parse("\n".join([_file_header(), _batch_header("CCD"), _entry("entry_detail_ccd")]))

    entry = result.batches[0].entries[0]
    assert entry.detail.layout == "entry_detail_ccd"
    assert entry.detail.fields["receiving_company_name"].value == "Jane Doe"
    assert "individual_name" not in entry.detail.fields


def test_parser_preserves_unknown_sec_without_ppd_fallback() -> None:
    entry_text = _entry("entry_detail_ppd")
    result = parse("\n".join([_file_header(), _batch_header("ZZZ"), entry_text]))

    detail = result.batches[0].entries[0].detail
    assert detail.layout == "unknown"
    assert detail.fields == {}
    assert detail.raw == entry_text


def test_parser_only_marks_all_nines_as_padding_after_file_control() -> None:
    batch_control, file_control = _controls()
    text = "\n".join([_file_header(), _batch_header("WEB"), "9" * 94, batch_control, file_control, "9" * 94])

    result = parse(text)

    assert result.control is not None and result.control.line_number == 5
    assert [record.line_number for record in result.unparsed] == [3]
    assert [record.line_number for record in result.padding] == [6]
    assert result.unparsed[0].layout == "unknown"


def test_parser_attaches_unknown_addenda_without_parsing_fields() -> None:
    unknown_addenda = "712" + "X" * 91
    result = parse("\n".join([_file_header(), _batch_header("WEB"), _entry("entry_detail_web"), unknown_addenda]))

    addenda = result.batches[0].entries[0].addenda[0]
    assert addenda.layout == "unknown"
    assert addenda.fields == {}
    assert addenda.line_number == 4


def test_parser_keeps_shuffled_orphan_and_malformed_lines_without_raising() -> None:
    batch_control, file_control = _controls()
    text = "\n".join(
        [
            _entry("entry_detail_ppd", indicator=0),
            "X malformed",
            _file_header(),
            batch_control,
            _batch_header("CCD"),
            _entry("entry_detail_ccd", indicator=0)[:12],
            batch_control,
            file_control,
        ]
    )

    result = parse(text)

    assert result.line_count == 8
    assert [record.line_number for record in result.unparsed] == [1, 2, 4]
    assert result.header is not None and result.header.line_number == 3
    assert result.batches[0].entries[0].detail.layout == "entry_detail_ccd"
    assert result.batches[0].entries[0].detail.line_number == 6
    assert result.control is not None and result.control.line_number == 8
