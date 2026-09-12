"""Focused CORE-14 validator orchestration tests."""

from achlens.core.rules.structural import Finding, ValidationContext
from achlens.core.validator import validate


def _runner(*findings: Finding):
    def run(_context: ValidationContext) -> list[Finding]:
        return list(findings)

    return run


def _finding(rule_id: str, severity: str) -> Finding:
    return Finding(rule_id, severity, rule_id)


def test_validator_aggregates_all_severities_and_summary() -> None:
    report = validate(
        "",
        runners=(
            _runner(
                _finding("S014", "error"),
                _finding("S013", "warning"),
                _finding("X", "info"),
            ),
        ),
    )

    assert not report.valid
    assert report.counts == {"error": 1, "warning": 1, "info": 1}
    assert report.counts_by_rule == {"S014": 1, "S013": 1, "X": 1}
    assert [finding.rule_id for finding in report.findings] == ["S014", "S013", "X"]
    assert report.summary.line_count == 0
    assert report.summary.batch_count == 0


def test_min_severity_filters_findings_but_not_complete_counts() -> None:
    report = validate(
        "",
        min_severity="warning",
        runners=(
            _runner(
                _finding("E", "error"), _finding("W", "warning"), _finding("I", "info")
            ),
        ),
    )

    assert report.counts == {"error": 1, "warning": 1, "info": 1}
    assert [finding.rule_id for finding in report.findings] == ["E", "W"]
    assert not report.truncated


def test_findings_are_truncated_without_changing_counts_or_validity() -> None:
    report = validate(
        "",
        max_findings=2,
        runners=(_runner(*(_finding(f"S{i:03d}", "error") for i in range(5))),),
    )

    assert not report.valid
    assert report.counts["error"] == 5
    assert report.counts_by_rule == {f"S{i:03d}": 1 for i in range(5)}
    assert len(report.findings) == 2
    assert report.truncated


def test_rule_filter_limits_reported_and_counted_rules() -> None:
    report = validate(
        "",
        rule_ids={"KEEP"},
        runners=(_runner(_finding("KEEP", "warning"), _finding("DROP", "error")),),
    )

    assert report.valid
    assert report.counts == {"error": 0, "warning": 1, "info": 0}
    assert list(report.counts_by_rule) == ["KEEP"]


def test_invalid_validator_options_are_rejected() -> None:
    try:
        validate("", min_severity="verbose")
    except ValueError as error:
        assert "min_severity" in str(error)
    else:
        raise AssertionError("invalid severity was accepted")

    try:
        validate("", max_findings=-1)
    except ValueError as error:
        assert "max_findings" in str(error)
    else:
        raise AssertionError("negative max_findings was accepted")
