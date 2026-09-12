"""Mask sensitive values in parsed ACH data without changing the source."""

from copy import deepcopy

from .model import AchFile, Record

_SENSITIVE_FIELDS = frozenset(
    {
        "dfi_account_number",
        "individual_identification_number",
        "corrected_data",
    }
)


def _masked_value(value: object) -> object:
    if not isinstance(value, str) or not value:
        return value
    if len(value) <= 4:
        return "*" * len(value)
    return "*" * (len(value) - 4) + value[-4:]


def _records(ach_file: AchFile) -> list[Record]:
    records: list[Record] = []
    if ach_file.header is not None:
        records.append(ach_file.header)
    for batch in ach_file.batches:
        if batch.header is not None:
            records.append(batch.header)
        for entry in batch.entries:
            records.append(entry.detail)
            records.extend(entry.addenda)
        if batch.control is not None:
            records.append(batch.control)
    if ach_file.control is not None:
        records.append(ach_file.control)
    records.extend(ach_file.padding)
    records.extend(ach_file.unparsed)
    return records


def mask(ach_file: AchFile, *, reveal: bool = False) -> AchFile:
    """Return a copy of *ach_file* with sensitive parsed values masked.

    Set ``reveal=True`` to explicitly return the sensitive values unchanged.
    Unknown layouts and fields are ignored while all source objects and field
    metadata remain untouched.
    """
    masked = deepcopy(ach_file)
    if reveal:
        return masked

    for record in _records(masked):
        for name in _SENSITIVE_FIELDS:
            field = record.fields.get(name)
            if field is None:
                continue
            field.value = _masked_value(field.value)
            field.raw = _masked_value(field.raw)
            if 0 <= field.start <= field.end <= len(record.raw):
                replacement = _masked_value(record.raw[field.start : field.end])
                record.raw = (
                    record.raw[: field.start] + replacement + record.raw[field.end :]
                )

    return masked


mask_ach_file = mask
