"""Deterministic structural and field-level ACH file differences."""

from dataclasses import asdict, dataclass

from .masking import mask
from .parser import parse


@dataclass(frozen=True, slots=True)
class RecordDifference:
    line: int
    kind: str
    field: str | None
    left: str | int | None
    right: str | int | None


def _records(ach_file):
    records = []
    if ach_file.header:
        records.append(ach_file.header)
    for batch in ach_file.batches:
        if batch.header:
            records.append(batch.header)
        for entry in batch.entries:
            records.append(entry.detail)
            records.extend(entry.addenda)
        if batch.control:
            records.append(batch.control)
    if ach_file.control:
        records.append(ach_file.control)
    records.extend(ach_file.padding)
    records.extend(ach_file.unparsed)
    return records


def diff_ach_files(
    left: str, right: str, *, reveal_sensitive: bool = False
) -> dict[str, object]:
    """Compare two ACH files without changing or validating either input."""
    left_file = parse(left)
    right_file = parse(right)
    if not reveal_sensitive:
        left_file = mask(left_file)
        right_file = mask(right_file)
    left_records = _records(left_file)
    right_records = _records(right_file)
    differences: list[RecordDifference] = []
    for index in range(max(len(left_records), len(right_records))):
        if index >= len(left_records):
            record = right_records[index]
            differences.append(
                RecordDifference(
                    record.line_number, "added_record", None, None, record.record_type
                )
            )
            continue
        if index >= len(right_records):
            record = left_records[index]
            differences.append(
                RecordDifference(
                    record.line_number, "removed_record", None, record.record_type, None
                )
            )
            continue
        left_record = left_records[index]
        right_record = right_records[index]
        if left_record.record_type != right_record.record_type:
            differences.append(
                RecordDifference(
                    left_record.line_number,
                    "record_type",
                    None,
                    left_record.record_type,
                    right_record.record_type,
                )
            )
        names = sorted(set(left_record.fields) | set(right_record.fields))
        for name in names:
            left_field = left_record.fields.get(name)
            right_field = right_record.fields.get(name)
            left_value = left_field.value if left_field else None
            right_value = right_field.value if right_field else None
            if left_value != right_value:
                differences.append(
                    RecordDifference(
                        left_record.line_number, "field", name, left_value, right_value
                    )
                )
    return {
        "equal": not differences and left_file.line_count == right_file.line_count,
        "left_line_count": left_file.line_count,
        "right_line_count": right_file.line_count,
        "differences": [asdict(item) for item in differences],
        "masked": not reveal_sensitive,
    }


__all__ = ["RecordDifference", "diff_ach_files"]
