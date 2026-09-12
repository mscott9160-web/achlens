"""Internal first slice of the validation-only streaming path.

This module deliberately contains no public parse model. The scanner records
only physical-line facts; rule execution still uses the legacy context until
the rule-facing streaming adapter has parity coverage.
"""

from dataclasses import dataclass

from .lines import SplitLines, split_lines


@dataclass(frozen=True)
class StreamFacts:
    """Bounded facts collected while consuming the physical line stream."""

    line_count: int
    line_ending: str
    exact_line_count: int
    first_record_type: str
    last_record_type: str


def scan(text: str) -> tuple[SplitLines, StreamFacts]:
    """Consume the physical records once and retain only compact facts."""
    split = split_lines(text)
    exact_line_count = 0
    first_record_type = ""
    last_record_type = ""
    for line in split.records:
        record_type = line.content[:1]
        if not first_record_type:
            first_record_type = record_type
        last_record_type = record_type
        if line.length.value == "exact":
            exact_line_count += 1
    facts = StreamFacts(
        line_count=len(split.records),
        line_ending=split.line_ending.value,
        exact_line_count=exact_line_count,
        first_record_type=first_record_type,
        last_record_type=last_record_type,
    )
    return split, facts
