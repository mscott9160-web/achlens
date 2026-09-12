"""Lightweight validation-only snapshot types and parser."""

from dataclasses import dataclass
from typing import Literal

from .data.entry_codes import (
    CREDIT_CODES,
    DEBIT_CODES,
    PRENOTE_CODES,
    ZERO_DOLLAR_CODES,
)
from .layouts import FieldSpec, RecordLayout, default_layouts
from .lines import LineRecord, RecordLength, split_lines

RecordKind = Literal["1", "5", "6", "7", "8", "9", "padding", "unknown"]

FIELDS = frozenset(
    {
        "priority_code",
        "immediate_destination",
        "immediate_origin",
        "file_creation_date",
        "file_creation_time",
        "file_id_modifier",
        "record_size",
        "blocking_factor",
        "format_code",
        "service_class_code",
        "company_name",
        "company_identification",
        "standard_entry_class_code",
        "company_entry_description",
        "effective_entry_date",
        "settlement_date",
        "originator_status_code",
        "originating_dfi_identification",
        "batch_number",
        "transaction_code",
        "receiving_dfi_identification",
        "check_digit",
        "dfi_account_number",
        "amount",
        "individual_name",
        "receiving_company_name",
        "addenda_record_indicator",
        "trace_number",
        "payment_type_code",
        "addenda_type_code",
        "addenda_sequence_number",
        "entry_detail_sequence_number",
        "return_reason_code",
        "original_entry_trace_number",
        "change_code",
        "corrected_data",
        "message_authentication_code",
        "reserved",
        "entry_addenda_count",
        "entry_hash",
        "total_debit_entry_dollar_amount",
        "total_credit_entry_dollar_amount",
        "batch_count",
        "block_count",
    }
)


@dataclass(frozen=True, slots=True)
class ValidationField:
    name: str
    start: int
    end: int
    raw: str
    value: str | int | None


@dataclass(frozen=True, slots=True)
class ValidationLine:
    line_number: int
    raw: str
    content: str
    record_type: RecordKind
    length: RecordLength
    potential_trailing_space_loss: bool


@dataclass(frozen=True, slots=True)
class ValidationRecord:
    line: ValidationLine
    layout: str
    fields: dict[str, ValidationField]


@dataclass(frozen=True, slots=True)
class ValidationEntry:
    detail: ValidationRecord
    addenda: tuple[ValidationRecord, ...]
    transaction_code: int | None
    amount_cents: int | None
    receiving_dfi: int | None
    trace_number: str
    is_credit: bool | None
    is_debit: bool | None
    is_prenote: bool
    is_zero_dollar: bool


@dataclass(frozen=True, slots=True)
class BatchAggregates:
    entry_addenda_count: int
    entry_hash: int
    total_debit_cents: int
    total_credit_cents: int


@dataclass(frozen=True, slots=True)
class ValidationBatch:
    header: ValidationRecord | None
    entries: tuple[ValidationEntry, ...]
    control: ValidationRecord | None
    aggregates: BatchAggregates


@dataclass(frozen=True, slots=True)
class FileAggregates:
    batch_count: int
    entry_addenda_count: int
    entry_hash: int
    total_debit_cents: int
    total_credit_cents: int
    block_count: int


@dataclass(frozen=True, slots=True)
class ValidationSnapshot:
    lines: tuple[ValidationLine, ...]
    line_count: int
    line_ending: str
    header: ValidationRecord | None
    batches: tuple[ValidationBatch, ...]
    file_control: ValidationRecord | None
    padding: tuple[ValidationLine, ...]
    unparsed: tuple[ValidationLine, ...]
    file_aggregates: FileAggregates


def _field_value(field: FieldSpec, content: str) -> ValidationField:
    raw = content[field.start - 1 : field.end]
    stripped = raw.strip()
    value: str | int | None = None
    if stripped:
        if field.type == "N":
            try:
                value = int(stripped)
            except ValueError:
                pass
        else:
            value = stripped.upper() if field.type == "A" else stripped
    return ValidationField(field.name, field.start, field.end, raw, value)


def _record(
    line: LineRecord, kind: RecordKind, layout: RecordLayout | None
) -> ValidationRecord:
    fields = (
        {
            field.name: _field_value(field, line.content)
            for field in layout.fields
            if field.name in FIELDS
        }
        if layout
        else {}
    )
    return ValidationRecord(
        ValidationLine(
            line.line_number,
            line.raw,
            line.content,
            kind,
            line.length,
            line.potential_trailing_space_loss,
        ),
        layout.name if layout else "unknown",
        fields,
    )


def _raw(record: ValidationRecord | None, name: str) -> str:
    field = record.fields.get(name) if record else None
    return field.raw if field else ""


def _integer(record: ValidationRecord | None, name: str) -> int | None:
    field = record.fields.get(name) if record else None
    return field.value if field and isinstance(field.value, int) else None


def _entry(
    detail: ValidationRecord, addenda: tuple[ValidationRecord, ...]
) -> ValidationEntry:
    code = _integer(detail, "transaction_code")
    amount = _integer(detail, "amount")
    return ValidationEntry(
        detail,
        addenda,
        code,
        amount,
        _integer(detail, "receiving_dfi_identification"),
        _raw(detail, "trace_number"),
        code in CREDIT_CODES if code is not None else None,
        code in DEBIT_CODES if code is not None else None,
        code in PRENOTE_CODES,
        code in ZERO_DOLLAR_CODES,
    )


def _batch_aggregates(entries: list[ValidationEntry]) -> BatchAggregates:
    count = sum(1 + len(entry.addenda) for entry in entries)
    entry_hash = sum(entry.receiving_dfi or 0 for entry in entries) % 10_000_000_000
    debit = sum(
        entry.amount_cents or 0
        for entry in entries
        if entry.is_debit and not entry.is_prenote and not entry.is_zero_dollar
    )
    credit = sum(
        entry.amount_cents or 0
        for entry in entries
        if entry.is_credit and not entry.is_prenote and not entry.is_zero_dollar
    )
    return BatchAggregates(count, entry_hash, debit, credit)


def build_validation_snapshot(text: str) -> ValidationSnapshot:
    """Build a validation-only snapshot without public FieldValue objects."""
    layouts = default_layouts()
    split = split_lines(text)
    lines = tuple(
        ValidationLine(
            item.line_number,
            item.raw,
            item.content,
            item.content[:1] if item.content[:1] in "156789" else "unknown",
            item.length,
            item.potential_trailing_space_loss,
        )
        for item in split.records
    )
    header: ValidationRecord | None = None
    batches: list[ValidationBatch] = []
    current_header: ValidationRecord | None = None
    entries: list[ValidationEntry] = []
    addenda: list[ValidationRecord] = []
    control: ValidationRecord | None = None
    file_control: ValidationRecord | None = None
    padding: list[ValidationLine] = []
    unparsed: list[ValidationLine] = []
    entry_layout: str | None = None
    after_control = False

    def flush_addenda() -> None:
        nonlocal addenda
        if addenda and entries:
            last = entries[-1]
            entries[-1] = _entry(last.detail, last.addenda + tuple(addenda))
            addenda = []

    def close_batch() -> None:
        nonlocal current_header, entries, addenda, control
        if current_header is not None:
            flush_addenda()
            batches.append(
                ValidationBatch(
                    current_header, tuple(entries), control, _batch_aggregates(entries)
                )
            )
        current_header = None
        entries = []
        addenda = []
        control = None

    for source in split.records:
        code = source.content[:1]
        if after_control and source.content == "9" * 94:
            padding.append(
                ValidationLine(
                    source.line_number,
                    source.raw,
                    source.content,
                    "padding",
                    source.length,
                    source.potential_trailing_space_loss,
                )
            )
        elif code == "1" and header is None:
            header = _record(source, "1", layouts["file_header"])
        elif code == "5" and (current_header is None or control is not None):
            close_batch()
            current_header = _record(source, "5", layouts["batch_header"])
            entry_layout = {
                "PPD": "entry_detail_ppd",
                "CCD": "entry_detail_ccd",
                "CTX": "entry_detail_ccd",
                "TEL": "entry_detail_web",
                "WEB": "entry_detail_web",
            }.get(_raw(current_header, "standard_entry_class_code"))
        elif (
            code == "6"
            and current_header is not None
            and control is None
            and entry_layout
        ):
            flush_addenda()
            entries.append(_entry(_record(source, "6", layouts[entry_layout]), tuple()))
        elif code == "7" and entries and control is None:
            layout_name = {
                "05": "addenda_05",
                "98": "addenda_98_noc",
                "99": "addenda_99_return",
            }.get(source.content[1:3])
            if layout_name:
                addenda.append(_record(source, "7", layouts[layout_name]))
            else:
                unparsed.append(
                    ValidationLine(
                        source.line_number,
                        source.raw,
                        source.content,
                        "unknown",
                        source.length,
                        source.potential_trailing_space_loss,
                    )
                )
        elif code == "8" and current_header is not None and control is None:
            flush_addenda()
            control = _record(source, "8", layouts["batch_control"])
        elif (
            code == "9"
            and file_control is None
            and control is not None
            and source.content != "9" * 94
        ):
            file_control = _record(source, "9", layouts["file_control"])
            after_control = True
        else:
            unparsed.append(
                ValidationLine(
                    source.line_number,
                    source.raw,
                    source.content,
                    code if code in "156789" else "unknown",
                    source.length,
                    source.potential_trailing_space_loss,
                )
            )
    close_batch()
    file_hash = sum(batch.aggregates.entry_hash for batch in batches) % 10_000_000_000
    file_debit = sum(batch.aggregates.total_debit_cents for batch in batches)
    file_credit = sum(batch.aggregates.total_credit_cents for batch in batches)
    entry_count = sum(batch.aggregates.entry_addenda_count for batch in batches)
    return ValidationSnapshot(
        lines,
        len(lines),
        split.line_ending.value.upper(),
        header,
        tuple(batches),
        file_control,
        tuple(padding),
        tuple(unparsed),
        FileAggregates(
            len(batches),
            entry_count,
            file_hash,
            file_debit,
            file_credit,
            (len(lines) + 9) // 10,
        ),
    )


def validation_context_from_snapshot(text: str, snapshot: ValidationSnapshot) -> object:
    """Adapt a snapshot to the existing rule context for parity tests."""
    from .model import AchFile, Batch, Entry, FieldValue, Record
    from .rules.structural import ValidationContext

    def record(source: ValidationRecord) -> Record:
        fields = {
            name: FieldValue(
                field.name,
                field.start,
                field.end,
                field.raw,
                field.value,
            )
            for name, field in source.fields.items()
        }
        return Record(
            source.line.line_number,
            source.line.record_type,
            source.layout,
            source.line.raw,
            fields,
        )

    batches: list[Batch] = []
    for batch in snapshot.batches:
        entries = [
            Entry(record(entry.detail), [record(addenda) for addenda in entry.addenda])
            for entry in batch.entries
        ]
        batches.append(
            Batch(
                header=record(batch.header) if batch.header else None,
                entries=entries,
                control=record(batch.control) if batch.control else None,
            )
        )
    ach_file = AchFile(
        header=record(snapshot.header) if snapshot.header else None,
        batches=batches,
        control=record(snapshot.file_control) if snapshot.file_control else None,
        padding=[
            Record(line.line_number, "padding", "", line.raw, {})
            for line in snapshot.padding
        ],
        line_count=snapshot.line_count,
        line_ending=snapshot.line_ending.lower(),
        unparsed=[
            Record(line.line_number, line.record_type, "unknown", line.raw, {})
            for line in snapshot.unparsed
        ],
    )
    return ValidationContext(text, split_lines(text), ach_file)


__all__ = [
    "ValidationSnapshot",
    "build_validation_snapshot",
    "validation_context_from_snapshot",
]
