"""Parity coverage for the internal first streaming-validation slice."""

from achlens.core import build_record, validate
from achlens.core.layouts import default_layouts
from achlens.core.rules.structural import Finding, ValidationContext
from tests.fixtures.builders import (
    inject_non_ascii,
    set_field,
    strip_trailing_spaces,
    valid_file,
)


def _validate(content: str, monkeypatch, enabled: bool):
    if enabled:
        monkeypatch.setenv("ACHLENS_INTERNAL_STREAMING_VALIDATION", "1")
    else:
        monkeypatch.delenv("ACHLENS_INTERNAL_STREAMING_VALIDATION", raising=False)
    return validate(content, min_severity="info", max_findings=200)


def test_streaming_flag_is_opt_in_and_default_matches_legacy(monkeypatch) -> None:
    content = valid_file()
    default_report = _validate(content, monkeypatch, False)
    streaming_report = _validate(content, monkeypatch, True)
    assert default_report == streaming_report


def test_streaming_matches_header_mutations(monkeypatch) -> None:
    content = valid_file()
    mutations = (
        set_field(content, 1, "file_header", "priority_code", 2),
        set_field(content, 2, "batch_header", "service_class_code", 999),
        set_field(content, 2, "batch_header", "effective_entry_date", 260231),
    )

    for mutated in (content, *mutations):
        legacy = _validate(mutated, monkeypatch, False)
        streaming = _validate(mutated, monkeypatch, True)
        assert streaming == legacy
        assert [finding.rule_id for finding in streaming.findings] == [
            finding.rule_id for finding in legacy.findings
        ]


def test_streaming_matches_control_mutations_and_truncation(monkeypatch) -> None:
    content = valid_file()
    mutations = (
        set_field(content, 4, "batch_control", "entry_addenda_count", 9),
        set_field(content, 4, "batch_control", "entry_hash", 99999999),
        set_field(content, 4, "batch_control", "total_debit_entry_dollar_amount", 1),
        set_field(content, 4, "batch_control", "total_credit_entry_dollar_amount", 1),
        set_field(content, 5, "file_control", "batch_count", 9),
        set_field(content, 5, "file_control", "entry_hash", 99999999),
        set_field(content, 5, "file_control", "total_credit_entry_dollar_amount", 1),
        set_field(content, 5, "file_control", "block_count", 9),
    )
    for mutated in mutations:
        for max_findings in (0, 1, 200):
            assert _validate(mutated, monkeypatch, True) == _validate(
                mutated, monkeypatch, False
            )
            monkeypatch.setenv("ACHLENS_INTERNAL_STREAMING_VALIDATION", "1")
            streaming = validate(
                mutated, min_severity="info", max_findings=max_findings
            )
            monkeypatch.delenv("ACHLENS_INTERNAL_STREAMING_VALIDATION", raising=False)
            legacy = validate(mutated, min_severity="info", max_findings=max_findings)
            assert streaming == legacy


def test_streaming_matches_mutated_and_malformed_fixtures(monkeypatch) -> None:
    mutations = (
        set_field(valid_file(), 3, "entry_detail_ppd", "amount", 999),
        inject_non_ascii(valid_file()),
        "\r\n".join(valid_file().splitlines()),
        "\n".join(
            [strip_trailing_spaces(valid_file().splitlines()[0])]
            + valid_file().splitlines()[1:]
        ),
    )
    for content in mutations:
        assert _validate(content, monkeypatch, True) == _validate(
            content, monkeypatch, False
        )


def test_custom_runner_falls_back_even_when_streaming_is_enabled(monkeypatch) -> None:
    finding = Finding("CUSTOM", "warning", "custom")

    def runner(_context: ValidationContext) -> list[Finding]:
        return [finding]

    monkeypatch.setenv("ACHLENS_INTERNAL_STREAMING_VALIDATION", "1")
    report = validate("", runners=(runner,))
    assert report.findings == [finding]
    assert report.counts_by_rule == {"CUSTOM": 1}


def test_streaming_matches_legacy_for_deterministic_malformed_corpus(
    monkeypatch,
) -> None:
    lines = valid_file().splitlines()
    cases = []
    for index in range(20):
        mutated = list(lines)
        mode = index % 5
        line_index = index % len(mutated)
        if mode == 0:
            mutated[line_index] = mutated[line_index][: max(0, 93 - index)]
        elif mode == 1:
            mutated[line_index] += "X" * (index + 1)
        elif mode == 2:
            mutated[line_index] = ("X" if index % 2 else "") + mutated[line_index][1:]
        elif mode == 3:
            mutated.insert(line_index, "8" + " " * 93)
        else:
            mutated[line_index] = mutated[line_index].replace(" ", "A", 1)
        cases.append("\n".join(mutated))

    for content in cases:
        assert _validate(content, monkeypatch, True) == _validate(
            content, monkeypatch, False
        )


def _with_addenda(sec: str, **values: object) -> str:
    content = set_field(
        valid_file(), 2, "batch_header", "standard_entry_class_code", sec
    )
    content = set_field(content, 3, "entry_detail_ppd", "addenda_record_indicator", 1)
    addenda_values = {
        "record_type_code": 7,
        "addenda_type_code": "05",
        "payment_related_information": "SENSITIVE-ACCOUNT-DATA",
        "addenda_sequence_number": 1,
        "entry_detail_sequence_number": 1,
        "return_reason_code": "R01",
        "original_entry_trace_number": "123456780000001",
        "change_code": "C01",
        "corrected_data": "UPDATED",
        **values,
    }
    layout_name = {
        "99": "addenda_99_return",
        "98": "addenda_98_noc",
    }.get(str(addenda_values["addenda_type_code"]), "addenda_05")
    layout_fields = {field.name for field in default_layouts()[layout_name].fields}
    addenda = build_record(
        default_layouts()[layout_name],
        **{
            name: value
            for name, value in addenda_values.items()
            if name in layout_fields
        },
    )
    lines = content.splitlines()
    lines.insert(3, addenda)
    return "\n".join(lines)


def test_streaming_matches_addenda_mutations_for_ppd_ccd_ctx_web_and_tel(monkeypatch):
    cases = [
        _with_addenda("PPD", addenda_sequence_number=2),
        _with_addenda("CCD", entry_detail_sequence_number=7654321),
        _with_addenda("CTX", addenda_type_code="77"),
        _with_addenda("WEB", addenda_type_code="77"),
        _with_addenda("TEL", addenda_type_code="77"),
    ]
    for content in cases:
        assert _validate(content, monkeypatch, True) == _validate(
            content, monkeypatch, False
        )


def test_streaming_matches_addenda_ordering_and_sensitive_values(monkeypatch):
    content = _with_addenda(
        "PPD",
        addenda_type_code="77",
        payment_related_information="ACCOUNT-1234-SECRET",
    )
    lines = content.splitlines()
    lines.insert(4, lines[3])
    malformed = "\r\n".join(lines[:4] + [lines[4]] + lines[5:])
    assert _validate(malformed, monkeypatch, True) == _validate(
        malformed, monkeypatch, False
    )
