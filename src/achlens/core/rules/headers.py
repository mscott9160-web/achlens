"""CORE-10 file-header and batch-header validation rules."""

import re
from collections.abc import Iterable
from datetime import datetime

from .registry import RuleRegistry, default_rule_registry
from .structural import Finding, Rule, ValidationContext, _finding

RECOGNIZED_SEC = frozenset({"CCD", "PPD", "WEB"})
RECOGNIZED_STANDARD_SEC = frozenset({"CCD", "CTX", "IAT", "PPD", "TEL", "WEB"})
RECOGNIZED_SERVICE_CLASSES = frozenset({"200", "220", "225"})
RECOGNIZED_ORIGINATOR_STATUSES = frozenset({"1", "2", "3"})
_DIGITS = re.compile(r"^\d+$")
_ALPHA_NUMERIC = re.compile(r"^[A-Z0-9]+$")


def _field(record, name: str):
    return record.fields.get(name) if record else None


def _raw(record, name: str) -> str:
    field = _field(record, name)
    return field.raw if field else ""


def _value(record, name: str) -> str:
    return _raw(record, name).strip().upper()


def _header_finding(
    rule_id: str,
    context: ValidationContext,
    message: str,
    *,
    line=None,
    position: int | None = None,
    severity: str | None = None,
) -> Finding:
    return _finding(
        rule_id,
        context,
        message,
        line=line,
        position=position,
        registry=header_rule_registry,
        severity=severity,
    )


def _valid_date(value: str) -> bool:
    try:
        datetime.strptime(value, "%y%m%d")
    except ValueError:
        return False
    return True


def fh001(context: ValidationContext) -> Iterable[Finding]:
    record = context.ach_file.header
    if _raw(record, "priority_code") != "01":
        yield _header_finding(
            "FH001", context, "Priority code must be 01.", line=record, position=2
        )


def fh002(context: ValidationContext) -> Iterable[Finding]:
    record = context.ach_file.header
    value = _value(record, "immediate_destination")
    if not (len(value) == 9 and value.isdigit()) and not (
        len(_raw(record, "immediate_destination")) == 10
        and _raw(record, "immediate_destination")[0] == " "
        and _raw(record, "immediate_destination")[1:].isdigit()
    ):
        yield _header_finding(
            "FH002",
            context,
            "Immediate destination must be blank-prefixed or a nine-digit "
            "routing number.",
            line=record,
            position=4,
        )


def fh003(context: ValidationContext) -> Iterable[Finding]:
    record = context.ach_file.header
    raw = _raw(record, "immediate_destination")
    routing = raw[1:] if len(raw) == 10 and raw[:1] == " " else raw
    if len(routing) == 9 and routing.isdigit():
        from ..calculators import valid_routing_number

        if not valid_routing_number(routing):
            yield _header_finding(
                "FH003",
                context,
                "Immediate destination routing check digit is invalid.",
                line=record,
                position=13,
            )


def fh004(context: ValidationContext) -> Iterable[Finding]:
    record = context.ach_file.header
    raw = _raw(record, "immediate_origin")
    if not (
        (len(raw) == 10 and raw[0] == " " and raw[1:].isdigit())
        or (len(raw.strip()) == 10 and raw.strip().isalnum())
    ):
        yield _header_finding(
            "FH004",
            context,
            "Immediate origin format is not recognized.",
            line=record,
            position=14,
        )


def fh005(context: ValidationContext) -> Iterable[Finding]:
    record = context.ach_file.header
    if not _valid_date(_raw(record, "file_creation_date")):
        yield _header_finding(
            "FH005",
            context,
            "File creation date must be a valid YYMMDD date.",
            line=record,
            position=24,
        )


def fh006(context: ValidationContext) -> Iterable[Finding]:
    record = context.ach_file.header
    value = _raw(record, "file_creation_time")
    if value.strip() and (
        len(value) != 4
        or not value.isdigit()
        or int(value[:2]) > 23
        or int(value[2:]) > 59
    ):
        yield _header_finding(
            "FH006",
            context,
            "File creation time must be a valid HHMM time when present.",
            line=record,
            position=30,
        )


def fh007(context: ValidationContext) -> Iterable[Finding]:
    record = context.ach_file.header
    if not _ALPHA_NUMERIC.fullmatch(_raw(record, "file_id_modifier")):
        yield _header_finding(
            "FH007",
            context,
            "File ID modifier must be an uppercase letter or digit.",
            line=record,
            position=34,
        )


def _exact_field(
    rule_id: str,
    context: ValidationContext,
    name: str,
    expected: str,
    position: int,
    label: str,
) -> Iterable[Finding]:
    record = context.ach_file.header
    if _raw(record, name) != expected:
        yield _header_finding(
            rule_id,
            context,
            f"{label} must be {expected}.",
            line=record,
            position=position,
        )


def fh008(context):
    yield from _exact_field("FH008", context, "record_size", "094", 35, "Record size")


def fh009(context):
    yield from _exact_field(
        "FH009", context, "blocking_factor", "10", 38, "Blocking factor"
    )


def fh010(context):
    yield from _exact_field("FH010", context, "format_code", "1", 40, "Format code")


def _batches(context):
    return ((batch.header, batch) for batch in context.ach_file.batches if batch.header)


def bh001(context):
    for record, _ in _batches(context):
        value = _value(record, "service_class_code")
        if value not in RECOGNIZED_SERVICE_CLASSES and value != "280":
            yield _header_finding(
                "BH001",
                context,
                "Service class code is not supported.",
                line=record,
                position=2,
            )
        elif value == "280":
            yield _header_finding(
                "BH001",
                context,
                "Service class code 280 is recognized but requires review.",
                line=record,
                position=2,
                severity="warning",
            )


def bh002(context):
    for record, _ in _batches(context):
        if not _value(record, "company_name"):
            yield _header_finding(
                "BH002",
                context,
                "Company name must not be blank.",
                line=record,
                position=5,
            )


def bh003(context):
    for record, _ in _batches(context):
        if not _value(record, "company_identification"):
            yield _header_finding(
                "BH003",
                context,
                "Company identification must not be blank.",
                line=record,
                position=41,
            )


def bh004(context):
    for record, _ in _batches(context):
        value = _value(record, "standard_entry_class_code")
        if value not in RECOGNIZED_SEC:
            severity = "warning" if value in RECOGNIZED_STANDARD_SEC else None
            yield _header_finding(
                "BH004",
                context,
                "SEC code is not recognized for v1.",
                line=record,
                position=51,
                severity=severity,
            )


def bh005(context):
    for record, _ in _batches(context):
        if not _value(record, "company_entry_description"):
            yield _header_finding(
                "BH005",
                context,
                "Company entry description must not be blank.",
                line=record,
                position=54,
            )


def bh006(context):
    for record, _ in _batches(context):
        if not _valid_date(_raw(record, "effective_entry_date")):
            yield _header_finding(
                "BH006",
                context,
                "Effective entry date must be a valid YYMMDD date.",
                line=record,
                position=70,
            )


def bh007(context):
    for record, _ in _batches(context):
        value = _raw(record, "effective_entry_date")
        if _valid_date(value) and datetime.strptime(value, "%y%m%d").weekday() >= 5:
            yield _header_finding(
                "BH007",
                context,
                "Effective entry date falls on a weekend.",
                line=record,
                position=70,
            )


def bh008(context):
    for record, _ in _batches(context):
        if _raw(record, "settlement_date").strip():
            yield _header_finding(
                "BH008",
                context,
                "Settlement date should be blank for origination input.",
                line=record,
                position=76,
            )


def bh009(context):
    for record, _ in _batches(context):
        if (
            _value(record, "originator_status_code")
            not in RECOGNIZED_ORIGINATOR_STATUSES
        ):
            yield _header_finding(
                "BH009",
                context,
                "Originator status code is not in the recognized catalog values.",
                line=record,
                position=79,
            )


def bh010(context):
    for record, _ in _batches(context):
        if not (
            _raw(record, "originating_dfi_identification").isdigit()
            and len(_raw(record, "originating_dfi_identification")) == 8
        ):
            yield _header_finding(
                "BH010",
                context,
                "ODFI identification must contain eight digits.",
                line=record,
                position=80,
            )


def bh011(context):
    previous = None
    for record, _ in _batches(context):
        value = _raw(record, "batch_number")
        if not value.isdigit() or (previous is not None and int(value) <= previous):
            yield _header_finding(
                "BH011", context, "Batch numbers must ascend.", line=record, position=88
            )
        if value.isdigit():
            previous = int(value)


header_rule_registry = RuleRegistry(
    spec
    for spec in default_rule_registry().specs.values()
    if spec.category in {"FH", "BH"}
)
_RULES: dict[str, Rule] = {
    f"FH{index:03d}": globals()[f"fh{index:03d}"] for index in range(1, 11)
}
_RULES.update({f"BH{index:03d}": globals()[f"bh{index:03d}"] for index in range(1, 12)})
for _rule_id, _function in _RULES.items():
    header_rule_registry.register(_rule_id, _function)
header_rule_registry.parity_check()


def validate_headers(context: ValidationContext | str) -> list[Finding]:
    if isinstance(context, str):
        context = ValidationContext.from_text(context)
    return [
        finding
        for rule in header_rule_registry.implementations.values()
        for finding in rule(context)
    ]


__all__ = [
    "header_rule_registry",
    "validate_headers",
    "RECOGNIZED_SEC",
    "RECOGNIZED_STANDARD_SEC",
    "RECOGNIZED_SERVICE_CLASSES",
    "RECOGNIZED_ORIGINATOR_STATUSES",
]
