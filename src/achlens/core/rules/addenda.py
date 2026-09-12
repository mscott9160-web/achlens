"""Addenda validation rules (AD001-AD008)."""

from collections.abc import Iterable

from ..model import Batch, Entry, Record
from .registry import RuleRegistry, default_rule_registry
from .structural import Finding, Rule, ValidationContext, _finding

KNOWN_RETURN_CODES = frozenset(
    {
        "R01",
        "R02",
        "R03",
        "R04",
        "R05",
        "R06",
        "R07",
        "R08",
        "R09",
        "R10",
        "R11",
        "R12",
        "R13",
        "R14",
        "R15",
        "R16",
        "R17",
        "R20",
        "R23",
        "R24",
        "R29",
    }
)
KNOWN_NOC_CODES = frozenset({"C01", "C02", "C03", "C04", "C05", "C06", "C07", "C09"})


def _value(record: Record, name: str) -> str:
    field = record.fields.get(name)
    return field.raw if field else ""


def _position(record: Record, name: str) -> int | None:
    field = record.fields.get(name)
    if field:
        return field.start
    return {
        "addenda_type_code": 2,
        "addenda_sequence_number": 84,
        "entry_detail_sequence_number": 88,
        "return_reason_code": 4,
        "original_entry_trace_number": 7,
        "change_code": 4,
        "corrected_data": 36,
    }.get(name)


def _emit(
    rule_id: str,
    context: ValidationContext,
    record: Record,
    message: str,
    field: str,
    *,
    severity: str | None = None,
) -> Finding:
    return _finding(
        rule_id,
        context,
        message,
        line=record,
        position=_position(record, field),
        severity=severity,
        registry=addenda_rule_registry,
    )


def _entries(context: ValidationContext) -> Iterable[tuple[Batch, Entry]]:
    for batch in context.ach_file.batches:
        for entry in batch.entries:
            yield batch, entry


def _sec(batch: Batch) -> str:
    return (
        _value(batch.header, "standard_entry_class_code").strip()
        if batch.header
        else ""
    )


def ad001(context: ValidationContext) -> Iterable[Finding]:
    for batch, entry in _entries(context):
        sec = _sec(batch)
        for addenda in entry.addenda:
            code = _value(addenda, "addenda_type_code")
            valid = code in {
                "PPD": {"05"},
                "CCD": {"05"},
                "CTX": {"05"},
                "WEB": {"05"},
                "RET": {"99"},
                "RETURN": {"99"},
                "NOC": {"98"},
            }.get(sec, set())
            if not valid:
                yield _emit(
                    "AD001",
                    context,
                    addenda,
                    "Addenda type is invalid for its context.",
                    "addenda_type_code",
                )


def ad002(context: ValidationContext) -> Iterable[Finding]:
    for batch, entry in _entries(context):
        if _sec(batch) in {"PPD", "CCD", "WEB"} and len(entry.addenda) > 1:
            for addenda in entry.addenda[1:]:
                yield _emit(
                    "AD002",
                    context,
                    addenda,
                    "PPD, CCD, and WEB entries may have at most one addenda record.",
                    "addenda_type_code",
                )


def ad003(context: ValidationContext) -> Iterable[Finding]:
    for batch, entry in _entries(context):
        if _sec(batch) in {"PPD", "CCD", "WEB"}:
            for addenda in entry.addenda:
                if (
                    _value(addenda, "addenda_type_code") == "05"
                    and _value(addenda, "addenda_sequence_number") != "0001"
                ):
                    yield _emit(
                        "AD003",
                        context,
                        addenda,
                        "Single-addenda sequence number must be 0001.",
                        "addenda_sequence_number",
                    )


def ad004(context: ValidationContext) -> Iterable[Finding]:
    for batch, entry in _entries(context):
        if _sec(batch) not in {"PPD", "CCD", "WEB"}:
            continue
        expected = _value(entry.detail, "trace_number")[-7:]
        for addenda in entry.addenda:
            if (
                _value(addenda, "addenda_type_code") == "05"
                and _value(addenda, "entry_detail_sequence_number") != expected
            ):
                yield _emit(
                    "AD004",
                    context,
                    addenda,
                    "Addenda entry-detail sequence number must match the last seven "
                    "digits of the parent trace number.",
                    "entry_detail_sequence_number",
                )


def ad005(context: ValidationContext) -> Iterable[Finding]:
    for _, entry in _entries(context):
        for addenda in entry.addenda:
            if (
                _value(addenda, "addenda_type_code") == "99"
                and _value(addenda, "return_reason_code") not in KNOWN_RETURN_CODES
            ):
                yield _emit(
                    "AD005",
                    context,
                    addenda,
                    "Return reason code is not recognized.",
                    "return_reason_code",
                    severity="warning",
                )


def ad006(context: ValidationContext) -> Iterable[Finding]:
    for _, entry in _entries(context):
        for addenda in entry.addenda:
            if _value(addenda, "addenda_type_code") == "99":
                value = _value(addenda, "original_entry_trace_number")
                if len(value) != 15 or not value.isdigit():
                    yield _emit(
                        "AD006",
                        context,
                        addenda,
                        "Original return trace number must be exactly 15 digits.",
                        "original_entry_trace_number",
                    )


def ad007(context: ValidationContext) -> Iterable[Finding]:
    for _, entry in _entries(context):
        for addenda in entry.addenda:
            if (
                _value(addenda, "addenda_type_code") == "98"
                and _value(addenda, "change_code") not in KNOWN_NOC_CODES
            ):
                yield _emit(
                    "AD007",
                    context,
                    addenda,
                    "NOC change code is not recognized.",
                    "change_code",
                    severity="warning",
                )


def ad008(context: ValidationContext) -> Iterable[Finding]:
    for _, entry in _entries(context):
        for addenda in entry.addenda:
            if (
                _value(addenda, "addenda_type_code") == "98"
                and not _value(addenda, "corrected_data").strip()
            ):
                yield _emit(
                    "AD008",
                    context,
                    addenda,
                    "NOC corrected data must not be blank.",
                    "corrected_data",
                )


_RULES: dict[str, Rule] = {
    f"AD{index:03d}": globals()[f"ad{index:03d}"] for index in range(1, 9)
}
addenda_rule_registry = RuleRegistry(
    spec for spec in default_rule_registry().specs.values() if spec.category == "AD"
)
for _rule_id, _function in _RULES.items():
    addenda_rule_registry.register(_rule_id, _function)
addenda_rule_registry.parity_check()


def validate_addenda(context: ValidationContext | str) -> list[Finding]:
    if isinstance(context, str):
        context = ValidationContext.from_text(context)
    return [
        finding
        for rule in addenda_rule_registry.implementations.values()
        for finding in rule(context)
    ]


__all__ = ["addenda_rule_registry", "validate_addenda"]
