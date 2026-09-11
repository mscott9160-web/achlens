"""Tolerant, layout-driven ACH parsing."""

from collections.abc import Mapping

from .layouts import FieldSpec, RecordLayout, default_layouts
from .lines import LineRecord, split_lines
from .model import AchFile, Batch, Entry, FieldValue, Record, RecordType


def _field_value(field: FieldSpec, content: str) -> FieldValue:
    raw = content[field.start - 1 : field.end]
    stripped = raw.strip()
    if not stripped:
        value: str | int | None = None
    elif field.type == "N":
        try:
            value = int(stripped)
        except ValueError:
            value = None
    else:
        value = stripped.upper() if field.type == "A" else stripped
    return FieldValue(
        field.name,
        field.start,
        field.end,
        raw,
        value,
        sensitive=bool(field.note and "SENSITIVE" in field.note.upper()),
    )


def _record(line: LineRecord, record_type: RecordType, layout: RecordLayout | None) -> Record:
    content = line.content
    return Record(
        line_number=line.line_number,
        record_type=record_type,
        layout=layout.name if layout else "",
        raw=line.raw,
        fields={field.name: _field_value(field, content) for field in layout.fields}
        if layout
        else {},
    )


def _unknown_record(line: LineRecord, record_type: RecordType) -> Record:
    record = _record(line, record_type, None)
    record.layout = "unknown"
    return record


def _layout_record(line: LineRecord, layouts: Mapping[str, RecordLayout], name: str,
                   record_type: RecordType) -> Record:
    return _record(line, record_type, layouts.get(name))


def parse(text: str, layouts: Mapping[str, RecordLayout] | None = None) -> AchFile:
    """Parse ACH text while retaining every source line and recovering structure."""
    layouts = layouts or default_layouts()
    split = split_lines(text)
    result = AchFile(
        line_count=len(split.records),
        line_ending=split.line_ending.value.upper() if split.line_ending.value != "mixed" else "mixed",
    )
    current_batch: Batch | None = None
    current_entry: Entry | None = None
    after_file_control = False

    for line in split.records:
        content = line.content
        code = content[:1]
        if after_file_control and content and set(content) == {"9"}:
            record = _record(line, "padding", None)
            result.padding.append(record)
            continue

        record: Record
        if code == "1" and result.header is None:
            record = _layout_record(line, layouts, "file_header", "1")
            result.header = record
        elif code == "5" and current_batch is None:
            record = _layout_record(line, layouts, "batch_header", "5")
            current_batch = Batch(header=record)
            result.batches.append(current_batch)
            current_entry = None
        elif code == "6" and current_batch is not None and current_batch.control is None:
            sec = current_batch.header.fields.get("standard_entry_class_code") if current_batch.header else None
            sec_code = sec.value if sec and isinstance(sec.value, str) else None
            layout_name = {"PPD": "entry_detail_ppd", "CCD": "entry_detail_ccd", "WEB": "entry_detail_web"}.get(sec_code)
            record = _layout_record(line, layouts, layout_name, "6") if layout_name else _unknown_record(line, "6")
            current_entry = Entry(record)
            current_batch.entries.append(current_entry)
        elif code == "7" and current_entry is not None and current_batch is not None and current_batch.control is None:
            addenda_code = content[1:3]
            layout_name = {"05": "addenda_05", "98": "addenda_98_noc", "99": "addenda_99_return"}.get(addenda_code)
            record = _layout_record(line, layouts, layout_name, "7") if layout_name else _unknown_record(line, "7")
            current_entry.addenda.append(record)
        elif code == "8" and current_batch is not None and current_batch.control is None:
            record = _layout_record(line, layouts, "batch_control", "8")
            current_batch.control = record
            current_entry = None
        elif code == "9" and result.control is None and (current_batch is None or current_batch.control is not None) and content != "9" * 94:
            record = _layout_record(line, layouts, "file_control", "9")
            result.control = record
            after_file_control = True
        else:
            record = _unknown_record(line, code if code in {"1", "5", "6", "7", "8", "9"} else "unknown")  # type: ignore[arg-type]
            result.unparsed.append(record)
    return result


parse_ach = parse