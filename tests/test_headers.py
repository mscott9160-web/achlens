"""CORE-10 file and batch header validation tests."""

from achlens.core import build_record
from achlens.core.layouts import default_layouts
from achlens.core.rules.headers import validate_headers


def _header(**overrides: object) -> str:
    values = dict(
        record_type_code=1,
        priority_code=1,
        immediate_destination=" 123456780",
        immediate_origin=" 987654321",
        file_creation_date=260911,
        file_creation_time=None,
        file_id_modifier="A",
        record_size=94,
        blocking_factor=10,
        format_code=1,
    )
    values.update(overrides)
    return build_record(default_layouts()["file_header"], **values)


def _batch(number: int = 1, **overrides: object) -> str:
    values = dict(
        record_type_code=5,
        service_class_code=200,
        company_name="Company",
        company_identification="1234567890",
        standard_entry_class_code="PPD",
        company_entry_description="PAYROLL",
        effective_entry_date=260911,
        settlement_date=None,
        originator_status_code=1,
        originating_dfi_identification=12345678,
        batch_number=number,
    )
    values.update(overrides)
    return build_record(default_layouts()["batch_header"], **values)


def _replace(record: str, start: int, end: int, value: str) -> str:
    return record[: start - 1] + value + record[end:]


def _findings(text: str):
    return validate_headers(text)


def test_valid_headers_have_no_core10_findings() -> None:
    findings = _findings("\n".join([_header(), _batch()]))
    assert findings == []


def test_file_header_rules_and_severities() -> None:
    cases = {
        "FH001": _replace(_header(), 2, 3, "02"),
        "FH002": _replace(_header(), 4, 13, "1234567890"),
        "FH003": _replace(_header(), 4, 13, " 123456781"),
        "FH004": _replace(_header(), 14, 23, "not-an-origin"),
        "FH005": _replace(_header(), 24, 29, "260231"),
        "FH006": _replace(_header(), 30, 33, "2460"),
        "FH007": _replace(_header(), 34, 34, "a"),
        "FH008": _replace(_header(), 35, 37, "095"),
        "FH009": _replace(_header(), 38, 39, "09"),
        "FH010": _replace(_header(), 40, 40, "2"),
    }
    for rule_id, header in cases.items():
        finding = next(f for f in _findings(header) if f.rule_id == rule_id)
        assert finding.position is not None
        assert finding.severity == (
            "warning"
            if rule_id == "FH001" or rule_id == "FH002"
            else "error"
            if rule_id not in {"FH004"}
            else "info"
        )


def test_batch_header_rules_and_severities() -> None:
    cases = {
        "BH001": _batch(service_class_code=999),
        "BH002": _replace(_batch(), 5, 20, " " * 16),
        "BH003": _replace(_batch(), 41, 50, " " * 10),
        "BH004": _batch(standard_entry_class_code="ZZZ"),
        "BH005": _replace(_batch(), 54, 63, " " * 10),
        "BH006": _replace(_batch(), 70, 75, "260231"),
        "BH007": _batch(effective_entry_date=260912),
        "BH008": _batch(settlement_date=1),
        "BH009": _batch(originator_status_code=9),
        "BH010": _replace(_batch(), 80, 87, "1234ABCD"),
    }
    for rule_id, batch in cases.items():
        finding = next(
            f for f in _findings("\n".join([_header(), batch])) if f.rule_id == rule_id
        )
        assert finding.position is not None
        expected = "warning" if rule_id in {"BH007", "BH008", "BH009"} else "error"
        assert finding.severity == expected


def test_service_class_280_is_a_warning() -> None:
    findings = [
        f
        for f in _findings("\n".join([_header(), _batch(service_class_code=280)]))
        if f.rule_id == "BH001"
    ]
    assert len(findings) == 1
    assert findings[0].severity == "warning"


def test_batch_numbers_must_ascend() -> None:
    batch_control = "8" + " " * 93
    findings = _findings(
        "\n".join(
            [_header(), _batch(2), batch_control, _batch(2), batch_control, _batch(1)]
        )
    )
    assert sum(f.rule_id == "BH011" for f in findings) == 2


def test_federal_reserve_holiday_is_a_warning() -> None:
    findings = _findings("\n".join([_header(), _batch(effective_entry_date=260704)]))
    holiday = next(f for f in findings if f.rule_id == "BH012")
    assert holiday.severity == "warning"


def test_unknown_sec_is_error_and_missing_sec_is_error() -> None:
    unknown = next(
        f
        for f in _findings(
            "\n".join([_header(), _batch(standard_entry_class_code="ZZZ")])
        )
        if f.rule_id == "BH004"
    )
    missing = _replace(_batch(), 51, 53, "   ")
    missing_finding = next(
        f for f in _findings("\n".join([_header(), missing])) if f.rule_id == "BH004"
    )
    assert unknown.severity == "error"
    assert missing_finding.severity == "error"


def test_recognized_standard_sec_outside_v1_is_warning() -> None:
    findings = _findings(
        "\n".join([_header(), _batch(standard_entry_class_code="CTX")])
    )
    bh004 = next(f for f in findings if f.rule_id == "BH004")
    assert bh004.severity == "warning"


def test_unknown_nonempty_sec_is_error() -> None:
    findings = _findings(
        "\n".join([_header(), _batch(standard_entry_class_code="ZZZ")])
    )
    bh004 = next(f for f in findings if f.rule_id == "BH004")
    assert bh004.severity == "error"
