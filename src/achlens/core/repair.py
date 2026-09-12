"""Safe repair of derived ACH control records and padding."""

from dataclasses import dataclass

from .calculators import (
    batch_entry_addenda_count,
    batch_entry_hash,
    batch_totals,
    file_entry_addenda_count,
    file_entry_hash,
    file_totals,
)
from .parser import parse
from .validator import validate


@dataclass(frozen=True)
class RepairChange:
    line: int
    field: str
    old: str
    new: str


@dataclass(frozen=True)
class RepairResult:
    repaired_content: str | None
    changes: list[RepairChange]
    refused: bool
    refusal_reason: str | None
    valid: bool


_BATCH_FIELDS = {
    "service_class_code": (2, 4),
    "entry_addenda_count": (5, 10),
    "entry_hash": (11, 20),
    "total_debit_entry_dollar_amount": (21, 32),
    "total_credit_entry_dollar_amount": (33, 44),
    "company_identification": (45, 54),
    "originating_dfi_identification": (80, 87),
    "batch_number": (88, 94),
}
_FILE_FIELDS = {
    "batch_count": (2, 7),
    "block_count": (8, 13),
    "entry_addenda_count": (14, 21),
    "entry_hash": (22, 31),
    "total_debit_entry_dollar_amount": (32, 43),
    "total_credit_entry_dollar_amount": (44, 55),
}


def _set_field(
    lines: list[str],
    line_number: int,
    field: str,
    start: int,
    end: int,
    value: object,
    changes: list[RepairChange],
) -> None:
    index = line_number - 1
    old = lines[index][start - 1 : end]
    new = str(value).zfill(end - start + 1)
    if old != new:
        lines[index] = lines[index][: start - 1] + new + lines[index][end:]
        changes.append(RepairChange(line_number, field, old, new))


def repair_control_records(
    content: str, *, restore_trailing_spaces: bool = True
) -> RepairResult:
    """Repair derived controls when record order is safe to rewrite."""
    structural = validate(content, rule_ids={"S006"})
    if structural.counts_by_rule.get("S006", 0):
        return RepairResult(
            None, [], True, "REPAIR_UNSAFE: record order is invalid", False
        )
    lines = content.splitlines()
    changes: list[RepairChange] = []
    if restore_trailing_spaces:
        for index, line in enumerate(lines):
            if len(line) < 94:
                new = line.ljust(94)
                changes.append(RepairChange(index + 1, "record_padding", line, new))
                lines[index] = new
    parsed = parse("\n".join(lines))
    for batch in parsed.batches:
        if batch.control is None:
            continue
        debit, credit = batch_totals(batch)
        values = {
            "service_class_code": batch.header.fields["service_class_code"].raw
            if batch.header
            else "",
            "entry_addenda_count": batch_entry_addenda_count(batch),
            "entry_hash": batch_entry_hash(batch),
            "total_debit_entry_dollar_amount": debit,
            "total_credit_entry_dollar_amount": credit,
            "company_identification": batch.header.fields["company_identification"].raw
            if batch.header
            else "",
            "originating_dfi_identification": batch.header.fields[
                "originating_dfi_identification"
            ].raw
            if batch.header
            else "",
            "batch_number": batch.header.fields["batch_number"].raw
            if batch.header
            else "",
        }
        for field, (start, end) in _BATCH_FIELDS.items():
            _set_field(
                lines,
                batch.control.line_number,
                field,
                start,
                end,
                values[field],
                changes,
            )
    parsed = parse("\n".join(lines))
    if parsed.control is not None:
        debit, credit = file_totals(parsed)
        values = {
            "batch_count": len(parsed.batches),
            "block_count": (len(lines) + 9) // 10,
            "entry_addenda_count": file_entry_addenda_count(parsed),
            "entry_hash": file_entry_hash(parsed),
            "total_debit_entry_dollar_amount": debit,
            "total_credit_entry_dollar_amount": credit,
        }
        for field, (start, end) in _FILE_FIELDS.items():
            _set_field(
                lines,
                parsed.control.line_number,
                field,
                start,
                end,
                values[field],
                changes,
            )
    substantive = [line for line in lines if line != "9" * 94]
    padding_needed = (-len(substantive)) % 10
    lines = substantive + ["9" * 94] * padding_needed
    repaired = "\n".join(lines)
    return RepairResult(repaired, changes, False, None, validate(repaired).valid)


__all__ = ["RepairChange", "RepairResult", "repair_control_records"]
