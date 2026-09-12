"""Structural validation rules for ACH files."""

from collections.abc import Iterable
from dataclasses import dataclass
from typing import Callable

from ..lines import LineRecord, SplitLines, split_lines
from ..model import AchFile, Record
from ..parser import parse
from .registry import RuleRegistry, default_rule_registry


@dataclass(frozen=True)
class Finding:
    rule_id: str
    severity: str
    message: str
    fix_hint: str | None = None
    line_number: int | None = None
    record_type: str | None = None
    position: int | None = None
    field: str | None = None
    expected: str | None = None
    actual: str | None = None


@dataclass(frozen=True)
class ValidationContext:
    """Parsed source and line metadata shared by structural rules."""

    text: str
    split: SplitLines
    ach_file: AchFile

    @classmethod
    def from_text(cls, text: str) -> "ValidationContext":
        lines = split_lines(text)
        return cls(text=text, split=lines, ach_file=parse(text))


Rule = Callable[[ValidationContext], Iterable[Finding]]


def _finding(
    rule_id: str,
    context: ValidationContext,
    message: str,
    *,
    line: LineRecord | Record | None = None,
    position: int | None = None,
    field: str | None = None,
    expected: str | None = None,
    actual: str | None = None,
    registry: RuleRegistry | None = None,
    severity: str | None = None,
) -> Finding:
    spec = (registry or structural_rule_registry).specs[rule_id]
    return Finding(
        rule_id=rule_id,
        severity=severity or spec.severity,
        message=message,
        fix_hint=spec.fix_hint or None,
        line_number=getattr(line, "line_number", None),
        record_type=getattr(line, "record_type", None),
        position=position,
        field=field,
        expected=expected,
        actual=actual,
    )


def _records(context: ValidationContext) -> tuple[LineRecord, ...]:
    return context.split.records


def _is_padding(line: LineRecord) -> bool:
    return line.content == "9" * 94


def _control_index(context: ValidationContext) -> int | None:
    records = _records(context)
    for index, line in enumerate(records):
        if line.content[:1] == "9" and not _is_padding(line):
            if index and records[index - 1].content[:1] in {"5", "6", "7", "8"}:
                return index
    return None


def s001(context: ValidationContext) -> Iterable[Finding]:
    for line in _records(context):
        if line.length.value != "exact":
            yield _finding(
                "S001",
                context,
                "Record line is not exactly 94 characters.",
                line=line,
                position=95,
            )


def s002(context: ValidationContext) -> Iterable[Finding]:
    for line in _records(context):
        if line.content.isascii() and line.content.isprintable():
            continue
        for offset, character in enumerate(line.content, start=1):
            if not 0x20 <= ord(character) <= 0x7E:
                yield _finding(
                    "S002",
                    context,
                    "Record contains non-printable ASCII.",
                    line=line,
                    position=offset,
                )
                break


def s003(context: ValidationContext) -> Iterable[Finding]:
    for line in _records(context):
        if not line.content or line.content[0] not in "156789":
            yield _finding(
                "S003", context, "Record type is unknown.", line=line, position=1
            )


def s004(context: ValidationContext) -> Iterable[Finding]:
    records = _records(context)
    if not records:
        yield _finding("S004", context, "File must begin with a file header.")
    elif records[0].content[:1] != "1":
        yield _finding(
            "S004", context, "File must begin with a file header.", line=records[0]
        )


def s005(context: ValidationContext) -> Iterable[Finding]:
    headers = [line for line in _records(context) if line.content[:1] == "1"]
    for line in headers[1:]:
        yield _finding(
            "S005", context, "File contains more than one file header.", line=line
        )


def s006(context: ValidationContext) -> Iterable[Finding]:
    valid = ("1", "5", "6", "7", "8", "9")
    previous = ""
    control_seen = False
    for line in _records(context):
        if _is_padding(line) and control_seen:
            continue
        code = line.content[:1]
        if code == "9" and not _is_padding(line):
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
            yield _finding("S006", context, "Record order is invalid.", line=line)
        if code in valid:
            previous = code


def s007(context: ValidationContext) -> Iterable[Finding]:
    for batch in context.ach_file.batches:
        if not batch.entries and batch.header:
            yield _finding(
                "S007",
                context,
                "Batch must contain at least one entry detail record.",
                line=batch.header,
            )


def s008(context: ValidationContext) -> Iterable[Finding]:
    if _control_index(context) is None:
        yield _finding("S008", context, "File control record is missing.")


def s009(context: ValidationContext) -> Iterable[Finding]:
    control_index = _control_index(context)
    if control_index is None:
        return
    for line in _records(context)[control_index + 1 :]:
        if not _is_padding(line):
            yield _finding(
                "S009",
                context,
                "Only padding may follow the file control record.",
                line=line,
            )


def s010(context: ValidationContext) -> Iterable[Finding]:
    control_index = _control_index(context)
    if control_index is None:
        return
    for line in _records(context)[control_index + 1 :]:
        if line.content[:1] == "9" and not _is_padding(line):
            yield _finding(
                "S010",
                context,
                "Padding record must contain exactly 94 nines.",
                line=line,
            )


def s011(context: ValidationContext) -> Iterable[Finding]:
    if context.ach_file.line_count % 10:
        yield _finding("S011", context, "Total record count must be a multiple of ten.")


def s012(context: ValidationContext) -> Iterable[Finding]:
    control_index = _control_index(context)
    if control_index is None:
        return
    actual = sum(_is_padding(line) for line in _records(context)[control_index + 1 :])
    expected = (10 - (control_index + 1) % 10) % 10
    if actual != expected:
        yield _finding(
            "S012", context, "Padding must fill the next ten-record block exactly."
        )


def s013(context: ValidationContext) -> Iterable[Finding]:
    if context.split.line_ending.value == "mixed":
        yield _finding("S013", context, "Record line endings are inconsistent.")


def s014(context: ValidationContext) -> Iterable[Finding]:
    if not _records(context):
        yield _finding("S014", context, "ACH file must contain at least one record.")


def _build_structural_rule_registry() -> RuleRegistry:
    specs = [
        spec for spec in default_rule_registry().specs.values() if spec.category == "S"
    ]
    registry = RuleRegistry(specs)
    for rule_id, function in _RULES.items():
        registry.register(rule_id, function)
    registry.parity_check()
    return registry


_RULES: dict[str, Rule] = {
    f"S{index:03d}": globals()[f"s{index:03d}"] for index in range(1, 15)
}
structural_rule_registry = _build_structural_rule_registry()


def validate_structure(context: ValidationContext | str) -> list[Finding]:
    """Run all registered structural rules against text or a context."""
    if isinstance(context, str):
        context = ValidationContext.from_text(context)
    return [
        finding
        for rule in structural_rule_registry.implementations.values()
        for finding in rule(context)
    ]


__all__ = [
    "Finding",
    "ValidationContext",
    "structural_rule_registry",
    "validate_structure",
]
