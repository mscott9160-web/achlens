"""Parity coverage for the internal first streaming-validation slice."""

from achlens.core import validate
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
