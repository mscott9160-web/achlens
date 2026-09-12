"""VPR-03 complete finding parity tests for the snapshot adapter."""

from achlens.core import generate_ach_file, validate
from achlens.core.validation_snapshot import (
    build_validation_snapshot,
    validation_context_from_snapshot,
)
from achlens.core.validator import validate as validate_context


def _finding_shape(report):
    return [
        (
            finding.rule_id,
            finding.severity,
            finding.line_number,
            finding.position,
            finding.field,
            finding.expected,
            finding.actual,
        )
        for finding in report.findings
    ]


def test_snapshot_context_matches_full_parser_findings() -> None:
    mutations = ([], ["ED004"], ["ED007"], ["ED012"], ["AD004"], ["BC002"], ["FC004"])
    for seed, inject_errors in enumerate(mutations):
        content = generate_ach_file(
            batches=2,
            entries_per_batch=2,
            include_prenotes=True,
            include_addenda=True,
            seed=seed,
            effective_date="260912",
            inject_errors=list(inject_errors),
        )
        full_report = validate(content)
        snapshot = build_validation_snapshot(content)
        adapted_report = validate_context(
            validation_context_from_snapshot(content, snapshot)
        )
        assert adapted_report.valid == full_report.valid
        assert adapted_report.counts == full_report.counts
        assert adapted_report.counts_by_rule == full_report.counts_by_rule
        assert _finding_shape(adapted_report) == _finding_shape(full_report)
