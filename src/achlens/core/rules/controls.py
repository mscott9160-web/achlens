"""Batch and file control-record validation rules (BC/FC)."""

from collections.abc import Iterable

from ..calculators import (
    batch_entry_addenda_count,
    batch_entry_hash,
    batch_totals,
    block_count,
    file_entry_addenda_count,
    file_entry_hash,
    file_totals,
)
from ..model import Batch, Record
from .registry import RuleRegistry, default_rule_registry
from .structural import Finding, Rule, ValidationContext, _finding


def _raw(record: Record | None, name: str) -> str:
    field = record.fields.get(name) if record else None
    return field.raw if field else ""


def _position(record: Record | None, name: str) -> int | None:
    field = record.fields.get(name) if record else None
    return field.start if field else None


def _emit(rule_id: str, context: ValidationContext, record: Record | None,
          field: str, expected: object, actual: str, message: str,
          *, severity: str | None = None) -> Finding:
    return _finding(rule_id, context, message, line=record,
                    position=_position(record, field), field=field,
                    expected=str(expected), actual=actual, severity=severity,
                    registry=control_rule_registry)


def _int(raw: str) -> int | None:
    return int(raw) if raw.isdigit() else None


def _batches(context: ValidationContext) -> Iterable[tuple[Batch, Record | None]]:
    for batch in context.ach_file.batches:
        yield batch, batch.control


def bc001(context: ValidationContext) -> Iterable[Finding]:
    for batch, control in _batches(context):
        expected = _raw(batch.header, "service_class_code")
        actual = _raw(control, "service_class_code")
        if actual != expected:
            yield _emit("BC001", context, control, "service_class_code", expected, actual, "Batch control service class does not match the header.")


def _batch_compare(context: ValidationContext, rule_id: str, batch: Batch, control: Record | None,
                   field: str, expected: int, message: str) -> Iterable[Finding]:
    actual = _raw(control, field)
    if _int(actual) != expected:
        yield _emit(rule_id, context, control, field, expected, actual, message)


def bc002(context: ValidationContext) -> Iterable[Finding]:
    for batch, control in _batches(context):
        yield from _batch_compare(context, "BC002", batch, control, "entry_addenda_count", batch_entry_addenda_count(batch), "Batch entry/addenda count does not match.")


def bc003(context: ValidationContext) -> Iterable[Finding]:
    for batch, control in _batches(context):
        yield from _batch_compare(context, "BC003", batch, control, "entry_hash", batch_entry_hash(batch), "Batch entry hash does not match.")


def bc004(context: ValidationContext) -> Iterable[Finding]:
    for batch, control in _batches(context):
        debit, _ = batch_totals(batch)
        yield from _batch_compare(context, "BC004", batch, control, "total_debit_entry_dollar_amount", debit, "Batch debit total does not match.")


def bc005(context: ValidationContext) -> Iterable[Finding]:
    for batch, control in _batches(context):
        _, credit = batch_totals(batch)
        yield from _batch_compare(context, "BC005", batch, control, "total_credit_entry_dollar_amount", credit, "Batch credit total does not match.")


def bc006(context: ValidationContext) -> Iterable[Finding]:
    for batch, control in _batches(context):
        expected = _raw(batch.header, "company_identification")
        actual = _raw(control, "company_identification")
        if actual != expected:
            yield _emit("BC006", context, control, "company_identification", expected, actual, "Batch control company identification does not match.")


def bc007(context: ValidationContext) -> Iterable[Finding]:
    for batch, control in _batches(context):
        expected = _raw(batch.header, "originating_dfi_identification")
        actual = _raw(control, "originating_dfi_identification")
        if actual != expected:
            yield _emit("BC007", context, control, "originating_dfi_identification", expected, actual, "Batch control ODFI identification does not match.")


def bc008(context: ValidationContext) -> Iterable[Finding]:
    for batch, control in _batches(context):
        expected = _raw(batch.header, "batch_number")
        actual = _raw(control, "batch_number")
        if actual != expected:
            yield _emit("BC008", context, control, "batch_number", expected, actual, "Batch control number does not match the header.")


def bc009(context: ValidationContext) -> Iterable[Finding]:
    for batch, control in _batches(context):
        for field in ("message_authentication_code", "reserved"):
            actual = _raw(control, field)
            if actual.strip():
                yield _emit("BC009", context, control, field, "blank", actual, "Batch control authentication/reserved field should be blank.", severity="warning")


def fc001(context: ValidationContext) -> Iterable[Finding]:
    control = context.ach_file.control
    expected = len(context.ach_file.batches)
    actual = _raw(control, "batch_count")
    if _int(actual) != expected:
        yield _emit("FC001", context, control, "batch_count", expected, actual, "File batch count does not match.")


def fc002(context: ValidationContext) -> Iterable[Finding]:
    control = context.ach_file.control
    expected = block_count(context.ach_file.line_count)
    actual = _raw(control, "block_count")
    if _int(actual) != expected:
        yield _emit("FC002", context, control, "block_count", expected, actual, "File block count does not match.")


def fc003(context: ValidationContext) -> Iterable[Finding]:
    control = context.ach_file.control
    expected = file_entry_addenda_count(context.ach_file)
    actual = _raw(control, "entry_addenda_count")
    if _int(actual) != expected:
        yield _emit("FC003", context, control, "entry_addenda_count", expected, actual, "File entry/addenda count does not match.")


def fc004(context: ValidationContext) -> Iterable[Finding]:
    control = context.ach_file.control
    expected = file_entry_hash(context.ach_file)
    actual = _raw(control, "entry_hash")
    if _int(actual) != expected:
        yield _emit("FC004", context, control, "entry_hash", expected, actual, "File entry hash does not match.")


def fc005(context: ValidationContext) -> Iterable[Finding]:
    control = context.ach_file.control
    expected, _ = file_totals(context.ach_file)
    actual = _raw(control, "total_debit_entry_dollar_amount")
    if _int(actual) != expected:
        yield _emit("FC005", context, control, "total_debit_entry_dollar_amount", expected, actual, "File debit total does not match.")


def fc006(context: ValidationContext) -> Iterable[Finding]:
    control = context.ach_file.control
    _, expected = file_totals(context.ach_file)
    actual = _raw(control, "total_credit_entry_dollar_amount")
    if _int(actual) != expected:
        yield _emit("FC006", context, control, "total_credit_entry_dollar_amount", expected, actual, "File credit total does not match.")


def fc007(context: ValidationContext) -> Iterable[Finding]:
    control = context.ach_file.control
    actual = _raw(control, "reserved")
    if actual.strip():
        yield _emit("FC007", context, control, "reserved", "blank", actual, "File control reserved field should be blank.", severity="warning")


_RULES: dict[str, Rule] = {f"BC{index:03d}": globals()[f"bc{index:03d}"] for index in range(1, 10)}
_RULES.update({f"FC{index:03d}": globals()[f"fc{index:03d}"] for index in range(1, 8)})
control_rule_registry = RuleRegistry(spec for spec in default_rule_registry().specs.values() if spec.category in {"BC", "FC"})
for _rule_id, _function in _RULES.items():
    control_rule_registry.register(_rule_id, _function)
control_rule_registry.parity_check()


def validate_controls(context: ValidationContext | str) -> list[Finding]:
    if isinstance(context, str):
        context = ValidationContext.from_text(context)
    return [finding for rule in control_rule_registry.implementations.values() for finding in rule(context)]


__all__ = ["control_rule_registry", "validate_controls"]