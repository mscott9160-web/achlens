"""Typed results produced by the tolerant ACH parser."""

from dataclasses import dataclass, field
from typing import Literal

RecordType = Literal["1", "5", "6", "7", "8", "9", "padding", "unknown"]


@dataclass(slots=True)
class FieldValue:
    name: str
    start: int
    end: int
    raw: str
    value: str | int | None
    sensitive: bool = False


@dataclass(slots=True)
class Record:
    line_number: int
    record_type: RecordType
    layout: str
    raw: str
    fields: dict[str, FieldValue] = field(default_factory=dict)


@dataclass(slots=True)
class Entry:
    detail: Record
    addenda: list[Record] = field(default_factory=list)


@dataclass(slots=True)
class Batch:
    header: Record | None = None
    entries: list[Entry] = field(default_factory=list)
    control: Record | None = None


@dataclass(slots=True)
class AchFile:
    header: Record | None = None
    batches: list[Batch] = field(default_factory=list)
    control: Record | None = None
    padding: list[Record] = field(default_factory=list)
    line_count: int = 0
    line_ending: Literal["LF", "CRLF", "mixed", "none"] = "none"
    unparsed: list[Record] = field(default_factory=list)
