"""Run all implemented ACH rules and build a bounded validation report."""

import os
from collections.abc import Callable
from dataclasses import dataclass, replace

from .parser import parse
from .rules.addenda import validate_addenda
from .rules.controls import validate_controls
from .rules.entry import validate_entries
from .rules.headers import validate_headers
from .rules.structural import Finding, ValidationContext, validate_structure
from .streaming import (
    StreamFacts,
    scan,
    validate_addenda_streaming,
    validate_controls_streaming,
    validate_entries_streaming,
    validate_headers_streaming,
    validate_structure_streaming,
)


@dataclass(frozen=True)
class FileSummary:
    """Small structural summary attached to every validation report."""

    line_count: int
    batch_count: int
    entry_count: int
    addenda_count: int


@dataclass(frozen=True)
class ValidationReport:
    """Complete aggregate counts plus a bounded list of findings."""

    valid: bool
    counts: dict[str, int]
    counts_by_rule: dict[str, int]
    findings: list[Finding]
    truncated: bool
    summary: FileSummary


RuleRunner = Callable[[ValidationContext], list[Finding]]
DEFAULT_RULE_RUNNERS: tuple[RuleRunner, ...] = (
    validate_structure,
    validate_headers,
    validate_entries,
    validate_addenda,
    validate_controls,
)
_SEVERITY_RANK = {"error": 0, "warning": 1, "info": 2}


def _streaming_enabled() -> bool:
    """Return whether the optimized internal validator path is enabled."""
    return os.environ.get("ACHLENS_DISABLE_STREAMING_VALIDATION") != "1"


def _streaming_context(content: str) -> tuple[ValidationContext, StreamFacts]:
    """Build the rule context after the bounded streaming scan."""
    split, facts = scan(content)
    return ValidationContext(
        text=content,
        split=split,
        ach_file=None,
    ), facts


def _summary(context: ValidationContext) -> FileSummary:
    batches = context.ach_file.batches
    return FileSummary(
        line_count=context.ach_file.line_count,
        batch_count=len(batches),
        entry_count=sum(len(batch.entries) for batch in batches),
        addenda_count=sum(
            len(entry.addenda) for batch in batches for entry in batch.entries
        ),
    )


def _streaming_summary(facts: StreamFacts) -> FileSummary:
    return FileSummary(
        line_count=facts.line_count,
        batch_count=facts.batch_count,
        entry_count=facts.entry_count,
        addenda_count=facts.addenda_count,
    )


def validate(
    content: str | ValidationContext,
    *,
    min_severity: str = "info",
    max_findings: int = 200,
    rule_ids: set[str] | None = None,
    runners: tuple[RuleRunner, ...] = DEFAULT_RULE_RUNNERS,
) -> ValidationReport:
    """Validate *content* and return every aggregate plus bounded findings.

    Counts are calculated from every rule result before severity filtering and
    truncation. ``valid`` is false whenever any error exists, even when the
    caller requests warnings or info findings to be hidden.
    """
    if min_severity not in _SEVERITY_RANK:
        raise ValueError("min_severity must be error, warning, or info")
    if max_findings < 0:
        raise ValueError("max_findings cannot be negative")
    use_streaming = (
        isinstance(content, str)
        and _streaming_enabled()
        and runners is DEFAULT_RULE_RUNNERS
    )
    if use_streaming:
        context, stream_facts = _streaming_context(content)
    else:
        context = (
            ValidationContext.from_text(content)
            if isinstance(content, str)
            else content
        )
    streaming_controls = use_streaming and (
        sum(line.content[:1] == "8" for line in context.split.records)
        == sum(line.content[:1] == "5" for line in context.split.records)
        and all(
            line.length.value == "exact"
            for line in context.split.records
            if line.content[:1] == "8"
            or (line.content[:1] == "9" and line.content != "9" * 94)
        )
    )
    if use_streaming and not streaming_controls:
        context = replace(context, ach_file=parse(content, split=context.split))
    all_findings = [
        finding
        for index, runner in enumerate(runners)
        for finding in (
            validate_structure_streaming(context.split)
            if use_streaming and index == 0
            else validate_headers_streaming(content, context.split)
            if use_streaming and index == 1
            else validate_entries_streaming(context.split)
            if use_streaming and index == 2
            else validate_addenda_streaming(context.split)
            if use_streaming and index == 3
            else validate_controls_streaming(context.split)
            if use_streaming and index == 4 and streaming_controls
            else runner(context)
        )
    ]
    if rule_ids is not None:
        all_findings = [
            finding for finding in all_findings if finding.rule_id in rule_ids
        ]

    counts = {severity: 0 for severity in ("error", "warning", "info")}
    counts_by_rule: dict[str, int] = {}
    for finding in all_findings:
        if finding.severity not in counts:
            raise ValueError(f"unknown finding severity: {finding.severity}")
        counts[finding.severity] += 1
        counts_by_rule[finding.rule_id] = counts_by_rule.get(finding.rule_id, 0) + 1

    visible = [
        finding
        for finding in all_findings
        if _SEVERITY_RANK[finding.severity] <= _SEVERITY_RANK[min_severity]
    ]
    findings = visible[:max_findings]
    return ValidationReport(
        valid=counts["error"] == 0,
        counts=counts,
        counts_by_rule=counts_by_rule,
        findings=findings,
        truncated=len(visible) > max_findings,
        summary=_streaming_summary(stream_facts)
        if use_streaming
        else _summary(context),
    )


validate_ach_file = validate


__all__ = [
    "DEFAULT_RULE_RUNNERS",
    "FileSummary",
    "ValidationReport",
    "validate",
    "validate_ach_file",
]
