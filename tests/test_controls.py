"""Focused CORE-13 batch and file control rule tests."""

from achlens.core import build_record
from achlens.core.layouts import default_layouts
from achlens.core.rules.controls import control_rule_registry, validate_controls


def _record(layout: str, **fields: object) -> str:
    return build_record(default_layouts()[layout], **fields)


def _file() -> str:
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
        company_entry_description="PAYROLL",
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
    padding = "9" * 94
    return "\n".join(
        [
            header,
            batch,
            entry,
            batch_control,
            file_control,
            padding,
            padding,
            padding,
            padding,
            padding,
        ]
    )


def _replace(record: str, start: int, end: int, value: str) -> str:
    return record[: start - 1] + value + record[end:]


def _findings(text: str):
    return validate_controls(text)


def test_registry_has_all_control_rules() -> None:
    assert set(control_rule_registry.specs) == {
        *(f"BC{i:03d}" for i in range(1, 10)),
        *(f"FC{i:03d}" for i in range(1, 8)),
    }
    assert set(control_rule_registry.implementations) == set(
        control_rule_registry.specs
    )


def test_balanced_file_has_no_control_findings() -> None:
    assert _findings(_file()) == []


def test_batch_control_mismatches_include_expected_actual_and_field() -> None:
    text = _file()
    lines = text.splitlines()
    lines[3] = _replace(lines[3], 5, 10, "000002")
    finding = next(f for f in _findings("\n".join(lines)) if f.rule_id == "BC002")
    assert finding.field == "entry_addenda_count"
    assert finding.expected == "1"
    assert finding.actual == "000002"
    assert finding.line_number == 4
    assert finding.position == 5


def test_file_control_mismatches_include_expected_actual() -> None:
    lines = _file().splitlines()
    lines[4] = _replace(lines[4], 22, 31, "0000000000")
    finding = next(f for f in _findings("\n".join(lines)) if f.rule_id == "FC004")
    assert finding.expected == "12345678"
    assert finding.actual == "0000000000"
    assert finding.field == "entry_hash"


def test_each_control_rule_has_a_trigger() -> None:
    cases = {
        "BC001": (3, 2, 4, "225"),
        "BC002": (3, 5, 10, "000002"),
        "BC003": (3, 11, 20, "0000000000"),
        "BC004": (3, 21, 32, "000000000001"),
        "BC005": (3, 33, 44, "000000000000"),
        "BC006": (3, 45, 54, "0000000000"),
        "BC007": (3, 80, 87, "00000000"),
        "BC008": (3, 88, 94, "0000002"),
        "BC009": (3, 74, 79, "ABC   "),
        "FC001": (4, 2, 7, "000002"),
        "FC002": (4, 8, 13, "000002"),
        "FC003": (4, 14, 21, "00000002"),
        "FC004": (4, 22, 31, "0000000000"),
        "FC005": (4, 32, 43, "000000000001"),
        "FC006": (4, 44, 55, "000000000000"),
        "FC007": (4, 56, 94, "RESERVED" + " " * 31),
    }
    for rule_id, (line_index, start, end, value) in cases.items():
        lines = _file().splitlines()
        lines[line_index] = _replace(lines[line_index], start, end, value)
        findings = _findings("\n".join(lines))
        assert any(f.rule_id == rule_id for f in findings), rule_id


def test_warning_control_rules_have_warning_severity() -> None:
    lines = _file().splitlines()
    lines[3] = _replace(lines[3], 55, 73, "AUTHENTICATION     ")
    lines[4] = _replace(lines[4], 56, 94, "RESERVED" + " " * 31)
    findings = _findings("\n".join(lines))
    assert next(f for f in findings if f.rule_id == "BC009").severity == "warning"
    assert next(f for f in findings if f.rule_id == "FC007").severity == "warning"
