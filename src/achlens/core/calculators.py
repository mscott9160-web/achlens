"""Pure calculations over parsed ACH records."""

from collections.abc import Iterable, Sequence

from .model import AchFile, Batch, Entry, FieldValue, Record

_ABA_WEIGHTS = (3, 7, 1, 3, 7, 1, 3, 7)
_CREDIT_CODES = frozenset({22, 23, 24, 32, 33, 34, 42, 43, 44, 52, 53, 54})
_DEBIT_CODES = frozenset({27, 28, 29, 37, 38, 39, 47, 48, 49, 55})
_PRENOTE_CODES = frozenset({23, 28, 33, 38, 43, 48})
_ZERO_DOLLAR_CODES = frozenset({24, 29, 34, 39, 44, 49, 54})


def _field(record: Record | None, name: str) -> FieldValue | None:
    return record.fields.get(name) if record is not None else None


def integer_field(record: Record | None, name: str) -> int | None:
    """Return a parsed integer field, or None when it is absent or invalid."""
    value = _field(record, name)
    return value.value if value is not None and isinstance(value.value, int) else None


def text_field(record: Record | None, name: str) -> str | None:
    """Return a parsed text field, or None when it is absent or blank/invalid."""
    value = _field(record, name)
    return value.value if value is not None and isinstance(value.value, str) and value.value else None


def aba_check_digit(first_eight: str) -> int:
    """Calculate the ABA check digit for exactly the first eight routing digits."""
    if len(first_eight) != 8 or not first_eight.isdigit():
        raise ValueError("routing prefix must contain exactly 8 digits")
    remainder = sum(int(digit) * weight for digit, weight in zip(first_eight, _ABA_WEIGHTS)) % 10
    return (10 - remainder) % 10


def valid_routing_number(routing_number: str) -> bool:
    """Return whether an eight-digit prefix or nine-digit ABA number is valid."""
    if len(routing_number) == 8 and routing_number.isdigit():
        return True
    return len(routing_number) == 9 and routing_number.isdigit() and int(routing_number[-1]) == aba_check_digit(routing_number[:8])


def _detail_hash(details: Iterable[Record]) -> int:
    total = 0
    for detail in details:
        value = integer_field(detail, "receiving_dfi_identification")
        if value is None:
            raise ValueError("receiving_dfi_identification must be numeric for a hashed detail")
        total += value
    return total


def batch_entry_hash(batch: Batch) -> int:
    """Sum detail RDFIs and retain the rightmost ten digits."""
    return _detail_hash(entry.detail for entry in batch.entries) % 10_000_000_000


def file_entry_hash(ach_file: AchFile) -> int:
    """Sum batch hashes and retain the rightmost ten digits."""
    return sum(batch_entry_hash(batch) for batch in ach_file.batches) % 10_000_000_000


def entry_addenda_count(records: Iterable[Record]) -> int:
    """Count entry and addenda records, excluding headers and controls."""
    return sum(record.record_type in {"6", "7"} for record in records)


def batch_entry_addenda_count(batch: Batch) -> int:
    return sum(1 + len(entry.addenda) for entry in batch.entries)


def file_entry_addenda_count(ach_file: AchFile) -> int:
    return sum(batch_entry_addenda_count(batch) for batch in ach_file.batches)


def _totals(entries: Iterable[Entry]) -> tuple[int, int]:
    debit = credit = 0
    for entry in entries:
        code = integer_field(entry.detail, "transaction_code")
        if code not in _DEBIT_CODES and code not in _CREDIT_CODES:
            continue
        if code in _PRENOTE_CODES or code in _ZERO_DOLLAR_CODES:
            amount = 0
        else:
            amount = integer_field(entry.detail, "amount")
            if amount is None:
                raise ValueError("amount must be numeric for transaction_code field")
        if code in _DEBIT_CODES:
            debit += amount
        elif code in _CREDIT_CODES:
            credit += amount
    return debit, credit


def batch_totals(batch: Batch) -> tuple[int, int]:
    """Return (debit cents, credit cents) for a batch."""
    return _totals(batch.entries)


def file_totals(ach_file: AchFile) -> tuple[int, int]:
    """Return (debit cents, credit cents) summed across batches."""
    debit = credit = 0
    for batch in ach_file.batches:
        batch_debit, batch_credit = batch_totals(batch)
        debit += batch_debit
        credit += batch_credit
    return debit, credit


def block_count(line_count: int, *, require_multiple: bool = False) -> int:
    """Return blocks for a padded file; reject or round up non-multiples explicitly."""
    if line_count < 0:
        raise ValueError("line count cannot be negative")
    if require_multiple and line_count % 10:
        raise ValueError("line count must be a multiple of 10")
    return (line_count + 9) // 10