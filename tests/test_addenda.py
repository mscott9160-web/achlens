"""Focused CORE-12 addenda validation tests."""

from achlens.core.model import AchFile, Batch, Entry, FieldValue, Record
from achlens.core.rules.addenda import addenda_rule_registry, validate_addenda
from achlens.core.rules.structural import ValidationContext


def _record(layout: str, line: int, values: dict[str, str], record_type: str) -> Record:
    starts = {
        "addenda_type_code": 2, "addenda_sequence_number": 84,
        "entry_detail_sequence_number": 88, "return_reason_code": 4,
        "original_entry_trace_number": 7, "change_code": 4,
        "corrected_data": 36, "trace_number": 80,
    }
    fields = {
        name: FieldValue(name, starts.get(name, 1), starts.get(name, 1) + len(value) - 1, value, value)
        for name, value in values.items()
    }
    return Record(line, record_type, layout, "7" + " " * 93, fields)


def _context(sec: str, addenda: list[Record], trace: str = "123456780000001") -> ValidationContext:
    header = Record(2, "5", "batch_header", "5" + " " * 93, {
        "standard_entry_class_code": FieldValue("standard_entry_class_code", 51, 53, sec, sec),
    })
    detail = Record(3, "6", "entry_detail_ppd", "6" + " " * 93, {
        "trace_number": FieldValue("trace_number", 80, 94, trace, trace),
    })
    return ValidationContext("", None, AchFile(batches=[Batch(header, [Entry(detail, addenda)])]))  # type: ignore[arg-type]


def _ids(context: ValidationContext) -> set[str]:
    return {finding.rule_id for finding in validate_addenda(context)}


def _05(**overrides: str) -> Record:
    values = {"addenda_type_code": "05", "addenda_sequence_number": "0001",
              "entry_detail_sequence_number": "0000001"}
    values.update(overrides)
    return _record("addenda_05", 4, values, "7")


def _99(**overrides: str) -> Record:
    values = {"addenda_type_code": "99", "return_reason_code": "R01",
              "original_entry_trace_number": "123456780000001"}
    values.update(overrides)
    return _record("addenda_99_return", 4, values, "7")


def _98(**overrides: str) -> Record:
    values = {"addenda_type_code": "98", "change_code": "C01",
              "original_entry_trace_number": "123456780000001", "corrected_data": "UPDATED"}
    values.update(overrides)
    return _record("addenda_98_noc", 4, values, "7")


def _other(**overrides: str) -> Record:
    values = {"addenda_type_code": "77"}
    values.update(overrides)
    return _record("addenda_other", 4, values, "7")


def test_registry_has_exactly_all_addenda_rules() -> None:
    assert set(addenda_rule_registry.specs) == {f"AD{i:03d}" for i in range(1, 9)}
    assert set(addenda_rule_registry.implementations) == set(addenda_rule_registry.specs)


def test_valid_ppd_ccd_web_addenda_and_parent_trace_linkage() -> None:
    for sec in ("PPD", "CCD", "WEB"):
        assert not _ids(_context(sec, [_05()]))
    assert "AD004" in _ids(_context("PPD", [_05(entry_detail_sequence_number="7654321")]))


def test_ad001_ad002_and_ad003() -> None:
    assert "AD001" in _ids(_context("PPD", [_05(addenda_type_code="07")]))
    assert "AD002" in _ids(_context("PPD", [_05(), _05()]))
    assert "AD002" in _ids(_context("PPD", [_05(), _other()]))
    assert "AD003" in _ids(_context("PPD", [_05(addenda_sequence_number="1")]))


def test_ad001_allows_only_context_specific_addenda_types() -> None:
    for sec, valid in (("PPD", "05"), ("CCD", "05"), ("WEB", "05"),
                       ("RET", "99"), ("RETURN", "99"), ("NOC", "98")):
        assert "AD001" not in _ids(_context(sec, [_record("addenda", 4, {"addenda_type_code": valid}, "7")]))
        invalid = "98" if valid == "99" else "99"
        assert "AD001" in _ids(_context(sec, [_record("addenda", 4, {"addenda_type_code": invalid}, "7")]))
    assert "AD001" in _ids(_context("CTX", [_05()]))


def test_return_addenda_recognizes_codes_and_requires_fifteen_digit_trace() -> None:
    assert not _ids(_context("RET", [_99()]))
    findings = validate_addenda(_context("RET", [_99(return_reason_code="R99", original_entry_trace_number="123")]))
    assert {finding.rule_id for finding in findings} == {"AD005", "AD006"}
    assert all(finding.severity == "warning" for finding in findings if finding.rule_id == "AD005")


def test_noc_addenda_recognizes_codes_and_requires_corrected_data() -> None:
    assert not _ids(_context("NOC", [_98()]))
    findings = validate_addenda(_context("NOC", [_98(change_code="C99", corrected_data="   ")]))
    assert {finding.rule_id for finding in findings} == {"AD007", "AD008"}
    assert next(f for f in findings if f.rule_id == "AD007").severity == "warning"


def test_reference_code_sets_use_only_appendix_seed_codes() -> None:
    assert "AD005" not in _ids(_context("RET", [_99(return_reason_code="R20")]))
    assert "AD005" in _ids(_context("RET", [_99(return_reason_code="R18")]))
    assert "AD007" not in _ids(_context("NOC", [_98(change_code="C09")]))
    assert "AD007" in _ids(_context("NOC", [_98(change_code="C08")]))


def test_malformed_widths_and_findings_include_line_and_field_position() -> None:
    findings = validate_addenda(_context("PPD", [_05(addenda_sequence_number="001", entry_detail_sequence_number="1")]))
    assert {finding.rule_id for finding in findings} == {"AD003", "AD004"}
    assert all(finding.line_number == 4 and finding.position is not None for finding in findings)