"""Entry-detail validation rules (ED001-ED016)."""

from collections.abc import Iterable

from ..calculators import aba_check_digit
from ..data.entry_codes import (
    CREDIT_CODES,
    DEBIT_CODES,
    PRENOTE_CODES,
    TRANSACTION_CODES,
    WEB_PAYMENT_TYPE_CODES,
    ZERO_DOLLAR_CODES,
)
from ..model import Batch, Entry, Record
from .registry import RuleRegistry, default_rule_registry
from .structural import Finding, Rule, ValidationContext, _finding


def _value(record: Record, name: str) -> str:
    field = record.fields.get(name)
    return field.raw if field else ""


def _position(record: Record, name: str) -> int | None:
    field = record.fields.get(name)
    return field.start if field else None


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
        registry=entry_rule_registry,
    )


def _number(raw: str) -> int | None:
    return int(raw) if raw and raw.isdigit() else None


def _entries(context: ValidationContext) -> Iterable[tuple[Batch, Entry]]:
    for batch in context.ach_file.batches:
        for entry in batch.entries:
            yield batch, entry


def ed001(context: ValidationContext) -> Iterable[Finding]:
    for _, entry in _entries(context):
        raw = _value(entry.detail, "transaction_code")
        if _number(raw) not in TRANSACTION_CODES:
            yield _emit(
                "ED001",
                context,
                entry.detail,
                "Transaction code is invalid.",
                "transaction_code",
            )


def ed002(context: ValidationContext) -> Iterable[Finding]:
    for batch, entry in _entries(context):
        code = _number(_value(entry.detail, "transaction_code"))
        service = (
            _number(_value(batch.header, "service_class_code"))
            if batch.header
            else None
        )
        invalid = (
            service == 220
            and code in DEBIT_CODES
            or service == 225
            and code in CREDIT_CODES
        )
        if invalid:
            yield _emit(
                "ED002",
                context,
                entry.detail,
                "Transaction code disagrees with the batch service class.",
                "transaction_code",
            )


def ed003(context: ValidationContext) -> Iterable[Finding]:
    for _, entry in _entries(context):
        rdfi = _value(entry.detail, "receiving_dfi_identification")
        if len(rdfi) != 8 or not rdfi.isdigit():
            yield _emit(
                "ED003",
                context,
                entry.detail,
                "Receiving DFI identification must be 8 digits.",
                "receiving_dfi_identification",
            )


def ed004(context: ValidationContext) -> Iterable[Finding]:
    for _, entry in _entries(context):
        rdfi = _value(entry.detail, "receiving_dfi_identification")
        check = _value(entry.detail, "check_digit")
        if len(rdfi) == 8 and rdfi.isdigit() and not check:
            yield _emit(
                "ED004",
                context,
                entry.detail,
                "Routing check digit is missing.",
                "check_digit",
            )
        elif (
            len(rdfi) == 8
            and rdfi.isdigit()
            and (len(check) != 1 or not check.isdigit())
        ):
            yield _emit(
                "ED004",
                context,
                entry.detail,
                "Routing check digit must be one digit.",
                "check_digit",
            )
        elif len(rdfi) == 8 and rdfi.isdigit() and int(check) != aba_check_digit(rdfi):
            yield _emit(
                "ED004",
                context,
                entry.detail,
                "Routing check digit does not match.",
                "check_digit",
            )


def ed005(context: ValidationContext) -> Iterable[Finding]:
    for _, entry in _entries(context):
        raw = _value(entry.detail, "dfi_account_number")
        if not raw.strip():
            yield _emit(
                "ED005",
                context,
                entry.detail,
                "DFI account number must not be blank.",
                "dfi_account_number",
            )
        elif raw[:1].isspace():
            yield _emit(
                "ED005",
                context,
                entry.detail,
                "DFI account number has leading spaces.",
                "dfi_account_number",
                severity="warning",
            )


def ed006(context: ValidationContext) -> Iterable[Finding]:
    for _, entry in _entries(context):
        amount = _value(entry.detail, "amount")
        if len(amount) != 10 or not amount.isdigit():
            yield _emit(
                "ED006", context, entry.detail, "Amount must be numeric.", "amount"
            )


def ed007(context: ValidationContext) -> Iterable[Finding]:
    for _, entry in _entries(context):
        code = _number(_value(entry.detail, "transaction_code"))
        amount = _number(_value(entry.detail, "amount"))
        if code in PRENOTE_CODES | ZERO_DOLLAR_CODES and amount != 0:
            yield _emit(
                "ED007",
                context,
                entry.detail,
                "Prenote and zero-dollar entries must have amount zero.",
                "amount",
            )


def ed008(context: ValidationContext) -> Iterable[Finding]:
    for _, entry in _entries(context):
        code = _number(_value(entry.detail, "transaction_code"))
        if (
            code in TRANSACTION_CODES - PRENOTE_CODES - ZERO_DOLLAR_CODES
            and _number(_value(entry.detail, "amount")) == 0
        ):
            yield _emit(
                "ED008", context, entry.detail, "Live entry has amount zero.", "amount"
            )


def ed009(context: ValidationContext) -> Iterable[Finding]:
    for _, entry in _entries(context):
        field = (
            "receiving_company_name"
            if entry.detail.layout == "entry_detail_ccd"
            else "individual_name"
        )
        if not _value(entry.detail, field).strip():
            yield _emit(
                "ED009", context, entry.detail, "Entry name must not be blank.", field
            )


def ed010(context: ValidationContext) -> Iterable[Finding]:
    for _, entry in _entries(context):
        indicator = _value(entry.detail, "addenda_record_indicator")
        if indicator not in {"0", "1"} or (indicator == "1") != bool(entry.addenda):
            yield _emit(
                "ED010",
                context,
                entry.detail,
                "Addenda indicator must be 0 or 1 and agree with attached addenda.",
                "addenda_record_indicator",
            )


def ed011(context: ValidationContext) -> Iterable[Finding]:
    for _, entry in _entries(context):
        if (
            not _value(entry.detail, "trace_number").isdigit()
            or len(_value(entry.detail, "trace_number")) != 15
        ):
            yield _emit(
                "ED011",
                context,
                entry.detail,
                "Trace number must be 15 digits.",
                "trace_number",
            )


def ed012(context: ValidationContext) -> Iterable[Finding]:
    for batch in context.ach_file.batches:
        previous = None
        for entry in batch.entries:
            current = _number(_value(entry.detail, "trace_number"))
            if current is not None and previous is not None and current <= previous:
                yield _emit(
                    "ED012",
                    context,
                    entry.detail,
                    "Trace numbers must ascend within the batch.",
                    "trace_number",
                )
            if current is not None:
                previous = current


def ed013(context: ValidationContext) -> Iterable[Finding]:
    seen: set[str] = set()
    for _, entry in _entries(context):
        trace = _value(entry.detail, "trace_number")
        if trace in seen and trace:
            yield _emit(
                "ED013",
                context,
                entry.detail,
                "Trace number is not unique within the file.",
                "trace_number",
            )
        seen.add(trace)


def ed014(context: ValidationContext) -> Iterable[Finding]:
    for batch, entry in _entries(context):
        odfi = _value(batch.header, "odfi_identification") if batch.header else ""
        trace = _value(entry.detail, "trace_number")
        if odfi and trace and trace[:8] != odfi:
            yield _emit(
                "ED014",
                context,
                entry.detail,
                "Trace prefix does not match batch ODFI.",
                "trace_number",
            )


def ed015(context: ValidationContext) -> Iterable[Finding]:
    for batch, entry in _entries(context):
        sec = (
            _value(batch.header, "standard_entry_class_code").strip()
            if batch.header
            else ""
        )
        if (
            entry.detail.layout == "entry_detail_web"
            and _value(entry.detail, "payment_type_code").strip()
            not in WEB_PAYMENT_TYPE_CODES
            and not (
                sec == "TEL" and not _value(entry.detail, "payment_type_code").strip()
            )
        ):
            yield _emit(
                "ED015",
                context,
                entry.detail,
                "WEB payment type code is not in the allowed set.",
                "payment_type_code",
                severity="warning",
            )


def ed016(context: ValidationContext) -> Iterable[Finding]:
    for batch, entry in _entries(context):
        code = _number(_value(entry.detail, "transaction_code"))
        sec = (
            _value(batch.header, "standard_entry_class_code").strip()
            if batch.header
            else ""
        )
        if code in ZERO_DOLLAR_CODES and sec not in {"CCD", "CTX"}:
            yield _emit(
                "ED016",
                context,
                entry.detail,
                "Zero-dollar remittance code is outside CCD/CTX.",
                "transaction_code",
            )


_RULES: dict[str, Rule] = {
    f"ED{index:03d}": globals()[f"ed{index:03d}"] for index in range(1, 17)
}


def entry_rule_registry() -> RuleRegistry:
    registry = RuleRegistry(
        spec for spec in default_rule_registry().specs.values() if spec.category == "ED"
    )
    for rule_id, function in _RULES.items():
        registry.register(rule_id, function)
    registry.parity_check()
    return registry


entry_rule_registry = entry_rule_registry()


def _validate_entries_fast(context: ValidationContext) -> list[Finding]:
    findings_by_rule: dict[str, list[Finding]] = {
        rule_id: [] for rule_id in entry_rule_registry.implementations
    }
    previous_by_batch: dict[int, int | None] = {}
    seen_traces: set[str] = set()
    for batch_index, batch in enumerate(context.ach_file.batches):
        previous = previous_by_batch.get(batch_index)
        service = (
            _number(_value(batch.header, "service_class_code"))
            if batch.header
            else None
        )
        odfi = _value(batch.header, "odfi_identification") if batch.header else ""
        sec = (
            _value(batch.header, "standard_entry_class_code").strip()
            if batch.header
            else ""
        )
        for entry in batch.entries:
            record = entry.detail
            code_raw = _value(record, "transaction_code")
            code = _number(code_raw)
            if code not in TRANSACTION_CODES:
                findings_by_rule["ED001"].append(
                    _emit(
                        "ED001",
                        context,
                        record,
                        "Transaction code is invalid.",
                        "transaction_code",
                    )
                )
            if (service == 220 and code in DEBIT_CODES) or (
                service == 225 and code in CREDIT_CODES
            ):
                findings_by_rule["ED002"].append(
                    _emit(
                        "ED002",
                        context,
                        record,
                        "Transaction code disagrees with the batch service class.",
                        "transaction_code",
                    )
                )
            rdfi = _value(record, "receiving_dfi_identification")
            check = _value(record, "check_digit")
            if len(rdfi) != 8 or not rdfi.isdigit():
                findings_by_rule["ED003"].append(
                    _emit(
                        "ED003",
                        context,
                        record,
                        "Receiving DFI identification must be 8 digits.",
                        "receiving_dfi_identification",
                    )
                )
            elif not check:
                findings_by_rule["ED004"].append(
                    _emit(
                        "ED004",
                        context,
                        record,
                        "Routing check digit is missing.",
                        "check_digit",
                    )
                )
            elif len(check) != 1 or not check.isdigit():
                findings_by_rule["ED004"].append(
                    _emit(
                        "ED004",
                        context,
                        record,
                        "Routing check digit must be one digit.",
                        "check_digit",
                    )
                )
            elif int(check) != aba_check_digit(rdfi):
                findings_by_rule["ED004"].append(
                    _emit(
                        "ED004",
                        context,
                        record,
                        "Routing check digit does not match.",
                        "check_digit",
                    )
                )
            account = _value(record, "dfi_account_number")
            if not account.strip():
                findings_by_rule["ED005"].append(
                    _emit(
                        "ED005",
                        context,
                        record,
                        "DFI account number must not be blank.",
                        "dfi_account_number",
                    )
                )
            elif account[:1].isspace():
                findings_by_rule["ED005"].append(
                    _emit(
                        "ED005",
                        context,
                        record,
                        "DFI account number has leading spaces.",
                        "dfi_account_number",
                        severity="warning",
                    )
                )
            amount_raw = _value(record, "amount")
            amount = _number(amount_raw)
            if len(amount_raw) != 10 or not amount_raw.isdigit():
                findings_by_rule["ED006"].append(
                    _emit("ED006", context, record, "Amount must be numeric.", "amount")
                )
            if code in PRENOTE_CODES | ZERO_DOLLAR_CODES and amount != 0:
                findings_by_rule["ED007"].append(
                    _emit(
                        "ED007",
                        context,
                        record,
                        "Prenote and zero-dollar entries must have amount zero.",
                        "amount",
                    )
                )
            if (
                code in TRANSACTION_CODES - PRENOTE_CODES - ZERO_DOLLAR_CODES
                and amount == 0
            ):
                findings_by_rule["ED008"].append(
                    _emit(
                        "ED008",
                        context,
                        record,
                        "Live entry has amount zero.",
                        "amount",
                    )
                )
            name_field = (
                "receiving_company_name"
                if record.layout == "entry_detail_ccd"
                else "individual_name"
            )
            if not _value(record, name_field).strip():
                findings_by_rule["ED009"].append(
                    _emit(
                        "ED009",
                        context,
                        record,
                        "Entry name must not be blank.",
                        name_field,
                    )
                )
            indicator = _value(record, "addenda_record_indicator")
            if indicator not in {"0", "1"} or (indicator == "1") != bool(entry.addenda):
                findings_by_rule["ED010"].append(
                    _emit(
                        "ED010",
                        context,
                        record,
                        "Addenda indicator must be 0 or 1 and agree with "
                        "attached addenda.",
                        "addenda_record_indicator",
                    )
                )
            trace = _value(record, "trace_number")
            if not trace.isdigit() or len(trace) != 15:
                findings_by_rule["ED011"].append(
                    _emit(
                        "ED011",
                        context,
                        record,
                        "Trace number must be 15 digits.",
                        "trace_number",
                    )
                )
            current = _number(trace)
            if current is not None and previous is not None and current <= previous:
                findings_by_rule["ED012"].append(
                    _emit(
                        "ED012",
                        context,
                        record,
                        "Trace numbers must ascend within the batch.",
                        "trace_number",
                    )
                )
            if current is not None:
                previous = current
            if trace in seen_traces and trace:
                findings_by_rule["ED013"].append(
                    _emit(
                        "ED013",
                        context,
                        record,
                        "Trace number is not unique within the file.",
                        "trace_number",
                    )
                )
            seen_traces.add(trace)
            if odfi and trace and trace[:8] != odfi:
                findings_by_rule["ED014"].append(
                    _emit(
                        "ED014",
                        context,
                        record,
                        "Trace prefix does not match batch ODFI.",
                        "trace_number",
                    )
                )
            if (
                record.layout == "entry_detail_web"
                and _value(record, "payment_type_code").strip()
                not in WEB_PAYMENT_TYPE_CODES
                and not (
                    sec == "TEL" and not _value(record, "payment_type_code").strip()
                )
            ):
                findings_by_rule["ED015"].append(
                    _emit(
                        "ED015",
                        context,
                        record,
                        "WEB payment type code is not in the allowed set.",
                        "payment_type_code",
                        severity="warning",
                    )
                )
            if code in ZERO_DOLLAR_CODES and sec not in {"CCD", "CTX"}:
                findings_by_rule["ED016"].append(
                    _emit(
                        "ED016",
                        context,
                        record,
                        "Zero-dollar remittance code is outside CCD/CTX.",
                        "transaction_code",
                    )
                )
        previous_by_batch[batch_index] = previous
    return [
        finding
        for rule_id in entry_rule_registry.implementations
        for finding in findings_by_rule[rule_id]
    ]


def validate_entries(context: ValidationContext | str) -> list[Finding]:
    if isinstance(context, str):
        context = ValidationContext.from_text(context)
    return _validate_entries_fast(context)


__all__ = ["entry_rule_registry", "validate_entries"]
