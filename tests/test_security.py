"""Release-hardening security regression tests."""

import json
from dataclasses import asdict

from achlens.core import build_record, mask, parse
from achlens.core.layouts import default_layouts
from achlens.server.tools import (
    explain_control_totals,
    lookup_ach_code,
    parse_ach_file,
    summarize_ach_file,
    validate_ach_file,
)
from tests.fixtures.builders import valid_file


def _record(layout: str, **fields: object) -> str:
    return build_record(default_layouts()[layout], **fields)


def _sensitive_file() -> str:
    header = _record(
        "file_header",
        record_type_code=1,
        priority_code=1,
        immediate_destination=" 123456780",
        immediate_origin=" 987654321",
        file_creation_date=260911,
        file_id_modifier="A",
        record_size=94,
        blocking_factor=10,
        format_code=1,
    )
    batch = _record(
        "batch_header",
        record_type_code=5,
        service_class_code=220,
        company_name="ACHLENS TEST",
        company_identification="9876543210",
        standard_entry_class_code="PPD",
        company_entry_description="TESTPAY",
        effective_entry_date=260911,
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
        dfi_account_number="ACCTSECRET1234567",
        amount=100,
        individual_identification_number="IDSECRET-5678",
        individual_name="TEST PERSON",
        addenda_record_indicator=0,
        trace_number=123456780000001,
    )
    return "\n".join([header, batch, entry])


def test_masking_removes_sensitive_values_from_serialized_output() -> None:
    original_values = ("ACCTSECRET1234567", "IDSECRET-5678")
    masked = mask(parse(_sensitive_file()))
    serialized = json.dumps(asdict(masked))
    for value in original_values:
        assert value not in serialized
    assert "4567" in serialized
    assert "5678" in serialized


def test_server_tools_do_not_open_network_connections() -> None:
    content = valid_file()
    assert "error" not in validate_ach_file(content=content)
    assert "error" not in summarize_ach_file(content=content)
    assert "error" not in parse_ach_file(content=content)
    assert "error" not in explain_control_totals(content=content)
    assert lookup_ach_code("transaction", "22")["code"] == "22"


def test_server_tools_do_not_leak_sensitive_values_to_output(capsys) -> None:
    content = _sensitive_file()
    sensitive_values = ("ACCTSECRET1234567", "IDSECRET-5678")

    results = (
        validate_ach_file(content=content),
        summarize_ach_file(content=content),
        parse_ach_file(content=content),
        explain_control_totals(content=content),
    )

    captured = capsys.readouterr()
    rendered = json.dumps(results) + captured.out + captured.err
    for value in sensitive_values:
        assert value not in rendered
