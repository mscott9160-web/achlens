"""Internal first slice of the validation-only streaming path.

This module deliberately contains no public parse model. The scanner records
only physical-line facts; rule execution still uses the legacy context until
the rule-facing streaming adapter has parity coverage.
"""

from dataclasses import dataclass

from .calculators import aba_check_digit
from .data.entry_codes import (
    CREDIT_CODES,
    DEBIT_CODES,
    PRENOTE_CODES,
    TRANSACTION_CODES,
    WEB_PAYMENT_TYPE_CODES,
    ZERO_DOLLAR_CODES,
)
from .layouts import default_layouts
from .lines import SplitLines, split_lines
from .model import AchFile, Batch
from .parser import _layout_record
from .rules.entry import entry_rule_registry
from .rules.headers import validate_headers
from .rules.structural import Finding, ValidationContext, structural_rule_registry


@dataclass(frozen=True)
class StreamFacts:
    """Bounded facts collected while consuming the physical line stream."""

    line_count: int
    line_ending: str
    exact_line_count: int
    first_record_type: str
    last_record_type: str


def _stream_entry_finding(
    rule_id: str, line, message: str, position: int, severity: str | None = None
) -> Finding:
    spec = entry_rule_registry.specs[rule_id]
    return Finding(
        rule_id=rule_id,
        severity=severity or spec.severity,
        message=message,
        fix_hint=spec.fix_hint or None,
        line_number=line.line_number,
        record_type="6",
        position=position,
    )


def _slice(content: str, start: int, end: int) -> str:
    return content[start - 1 : end]


def validate_entries_streaming(split: SplitLines) -> list[Finding]:
    """Evaluate ED rules from fixed-width entry slices and compact parent state."""
    findings_by_rule: dict[str, list[Finding]] = {
        rule_id: [] for rule_id in entry_rule_registry.implementations
    }
    previous: int | None = None
    seen_traces: set[str] = set()
    service = None
    sec = ""
    odfi = ""
    pending_entry = None
    pending_addenda = 0

    def finish_entry(entry, addenda_count: int) -> None:
        nonlocal previous
        line, content, layout = entry

        def field(name: str) -> str:
            return _slice(content, *layout[name])

        code_raw = field("transaction_code")
        code = int(code_raw) if code_raw.isdigit() else None
        rdfi = field("receiving_dfi_identification")
        check = field("check_digit")
        account = field("dfi_account_number")
        amount_raw = field("amount")
        amount = int(amount_raw) if amount_raw.isdigit() else None
        trace = field("trace_number")

        def add(rule, message, name, severity=None):
            findings_by_rule[rule].append(
                _stream_entry_finding(rule, line, message, layout[name][0], severity)
            )

        if code not in TRANSACTION_CODES:
            add("ED001", "Transaction code is invalid.", "transaction_code")
        if (service == 220 and code in DEBIT_CODES) or (
            service == 225 and code in CREDIT_CODES
        ):
            add(
                "ED002",
                "Transaction code disagrees with the batch service class.",
                "transaction_code",
            )
        if len(rdfi) != 8 or not rdfi.isdigit():
            add(
                "ED003",
                "Receiving DFI identification must be 8 digits.",
                "receiving_dfi_identification",
            )
        elif not check:
            add("ED004", "Routing check digit is missing.", "check_digit")
        elif len(check) != 1 or not check.isdigit():
            add("ED004", "Routing check digit must be one digit.", "check_digit")
        elif int(check) != aba_check_digit(rdfi):
            add("ED004", "Routing check digit does not match.", "check_digit")
        if not account.strip():
            add("ED005", "DFI account number must not be blank.", "dfi_account_number")
        elif account[:1].isspace():
            add(
                "ED005",
                "DFI account number has leading spaces.",
                "dfi_account_number",
                "warning",
            )
        if len(amount_raw) != 10 or not amount_raw.isdigit():
            add("ED006", "Amount must be numeric.", "amount")
        if code in PRENOTE_CODES | ZERO_DOLLAR_CODES and amount != 0:
            add(
                "ED007",
                "Prenote and zero-dollar entries must have amount zero.",
                "amount",
            )
        if (
            code in TRANSACTION_CODES - PRENOTE_CODES - ZERO_DOLLAR_CODES
            and amount == 0
        ):
            add("ED008", "Live entry has amount zero.", "amount")
        name = (
            "receiving_company_name"
            if layout.get("receiving_company_name")
            else "individual_name"
        )
        if not field(name).strip():
            add("ED009", "Entry name must not be blank.", name)
        indicator = field("addenda_record_indicator")
        if indicator not in {"0", "1"} or (indicator == "1") != bool(addenda_count):
            add(
                "ED010",
                "Addenda indicator must be 0 or 1 and agree with attached addenda.",
                "addenda_record_indicator",
            )
        if not trace.isdigit() or len(trace) != 15:
            add("ED011", "Trace number must be 15 digits.", "trace_number")
        current = int(trace) if trace.isdigit() else None
        if current is not None and previous is not None and current <= previous:
            add("ED012", "Trace numbers must ascend within the batch.", "trace_number")
        if current is not None:
            previous = current
        if trace in seen_traces and trace:
            add("ED013", "Trace number is not unique within the file.", "trace_number")
        seen_traces.add(trace)
        if odfi and trace and trace[:8] != odfi:
            add("ED014", "Trace prefix does not match batch ODFI.", "trace_number")
        payment = (
            field("payment_type_code").strip()
            if layout.get("payment_type_code")
            else ""
        )
        if (
            layout.get("payment_type_code")
            and payment not in WEB_PAYMENT_TYPE_CODES
            and not (sec == "TEL" and not payment)
        ):
            add(
                "ED015",
                "WEB payment type code is not in the allowed set.",
                "payment_type_code",
                "warning",
            )
        if code in ZERO_DOLLAR_CODES and sec not in {"CCD", "CTX"}:
            add(
                "ED016",
                "Zero-dollar remittance code is outside CCD/CTX.",
                "transaction_code",
            )

    layouts = default_layouts()
    entry_layouts = {
        "PPD": layouts["entry_detail_ppd"],
        "CCD": layouts["entry_detail_ccd"],
        "WEB": layouts["entry_detail_web"],
    }
    for index, line in enumerate(split.records):
        code = line.content[:1]
        if code == "5":
            if pending_entry is not None:
                finish_entry(pending_entry, pending_addenda)
                pending_entry = None
                pending_addenda = 0
            previous = None
            service_raw = _slice(line.content, 2, 4)
            service = int(service_raw) if service_raw.isdigit() else None
            sec = _slice(line.content, 51, 53).strip()
            odfi = _slice(line.content, 80, 87)
        elif code == "6":
            if pending_entry is not None:
                finish_entry(pending_entry, pending_addenda)
            layout = entry_layouts.get(sec, layouts["entry_detail_ppd"])
            pending_entry = (
                line,
                line.content,
                {f.name: (f.start, f.end) for f in layout.fields},
            )
            pending_addenda = 0
        elif code == "7" and pending_entry is not None:
            pending_addenda += 1
        elif pending_entry is not None:
            finish_entry(pending_entry, pending_addenda)
            pending_entry = None
            pending_addenda = 0
            if code == "8":
                previous = None
    if pending_entry is not None:
        finish_entry(pending_entry, pending_addenda)
    return [
        finding
        for rule_id in entry_rule_registry.implementations
        for finding in findings_by_rule[rule_id]
    ]


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


def validate_headers_streaming(text: str, split: SplitLines) -> list[Finding]:
    """Evaluate FH/BH rules from header records in the physical line stream."""
    layouts = default_layouts()
    ach_file = AchFile(line_count=len(split.records))
    current_batch: Batch | None = None

    for line in split.records:
        code = line.content[:1]
        if code == "1" and ach_file.header is None:
            ach_file.header = _layout_record(line, layouts, "file_header", "1")
        elif code == "5" and (
            current_batch is None or current_batch.control is not None
        ):
            current_batch = Batch(
                header=_layout_record(line, layouts, "batch_header", "5")
            )
            ach_file.batches.append(current_batch)
        elif code == "8" and current_batch is not None:
            current_batch.control = _layout_record(line, layouts, "batch_control", "8")

    context = ValidationContext(text=text, split=split, ach_file=ach_file)
    return validate_headers(context)
