"""Internal first slice of the validation-only streaming path.

This module deliberately contains no public parse model. The scanner records
only physical-line facts; rule execution still uses the legacy context until
the rule-facing streaming adapter has parity coverage.
"""

from dataclasses import dataclass

from .lines import SplitLines, split_lines
from .rules.structural import Finding, structural_rule_registry


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


def validate_structure_streaming(split: SplitLines) -> list[Finding]:
    """Evaluate the structural rules from bounded line state only."""
    records = split.records
    findings: list[Finding] = []

    def add(
        rule_id: str,
        message: str,
        line=None,
        position: int | None = None,
        record_type: str | None = None,
    ):
        spec = structural_rule_registry.specs[rule_id]
        findings.append(
            Finding(
                rule_id=rule_id,
                severity=spec.severity,
                message=message,
                fix_hint=spec.fix_hint or None,
                line_number=getattr(line, "line_number", None),
                record_type=(
                    record_type
                    if record_type is not None
                    else getattr(line, "record_type", None)
                ),
                position=position,
            )
        )

    for line in records:
        if line.length.value != "exact":
            add("S001", "Record line is not exactly 94 characters.", line, 95)

    for line in records:
        if not (line.content.isascii() and line.content.isprintable()):
            for offset, character in enumerate(line.content, start=1):
                if not 0x20 <= ord(character) <= 0x7E:
                    add("S002", "Record contains non-printable ASCII.", line, offset)
                    break

    for line in records:
        if not line.content or line.content[0] not in "156789":
            add("S003", "Record type is unknown.", line, 1)

    if not records:
        add("S004", "File must begin with a file header.")
    elif records[0].content[:1] != "1":
        add("S004", "File must begin with a file header.", records[0])

    for line in records[1:]:
        if line.content[:1] == "1":
            add("S005", "File contains more than one file header.", line)

    valid = {"1", "5", "6", "7", "8", "9"}
    previous = ""
    control_seen = False
    for line in records:
        padding = line.content == "9" * 94
        if padding and control_seen:
            continue
        code = line.content[:1]
        if code == "9" and not padding:
            control_seen = True
        allowed = (
            (not previous and code == "1")
            or (previous == "1" and code == "5")
            or (previous == "5" and code in {"6", "8"})
            or (previous == "6" and code in {"6", "7", "8"})
            or (previous == "7" and code in {"7", "6", "8"})
            or (previous == "8" and code in {"5", "9"})
            or (previous == "9" and code == "9")
        )
        if code not in valid or (previous and not allowed):
            add("S006", "Record order is invalid.", line)
        if code in valid:
            previous = code

    batch_header = None
    batch_has_entry = False
    for line in records:
        code = line.content[:1]
        if code == "5":
            if batch_header is not None and not batch_has_entry:
                add(
                    "S007",
                    "Batch must contain at least one entry detail record.",
                    batch_header,
                    record_type="5",
                )
            batch_header = line
            batch_has_entry = False
        elif code == "6" and batch_header is not None:
            batch_has_entry = True
        elif code in {"8", "9"} and batch_header is not None:
            if not batch_has_entry:
                add(
                    "S007",
                    "Batch must contain at least one entry detail record.",
                    batch_header,
                    record_type="5",
                )
            batch_header = None

    control_index = next(
        (
            index
            for index, line in enumerate(records)
            if line.content[:1] == "9"
            and line.content != "9" * 94
            and index
            and records[index - 1].content[:1] in {"5", "6", "7", "8"}
        ),
        None,
    )
    if control_index is None:
        add("S008", "File control record is missing.")
    else:
        trailing = records[control_index + 1 :]
        for line in trailing:
            if line.content != "9" * 94:
                add("S009", "Only padding may follow the file control record.", line)
        for line in trailing:
            if line.content[:1] == "9" and line.content != "9" * 94:
                add("S010", "Padding record must contain exactly 94 nines.", line)

    if len(records) % 10:
        add("S011", "Total record count must be a multiple of ten.")
    if control_index is not None:
        actual = sum(line.content == "9" * 94 for line in records[control_index + 1 :])
        expected = (10 - (control_index + 1) % 10) % 10
        if actual != expected:
            add("S012", "Padding must fill the next ten-record block exactly.")
    if split.line_ending.value == "mixed":
        add("S013", "Record line endings are inconsistent.")
    if not records:
        add("S014", "ACH file must contain at least one record.")
    return findings
