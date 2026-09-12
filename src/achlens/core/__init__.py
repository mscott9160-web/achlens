"""Core ACH layout and parsing foundations."""

from .builder import build_record
from .diff import RecordDifference, diff_ach_files
from .generator import generate_ach_file
from .layouts import FieldSpec, RecordLayout, default_layouts, load_layouts
from .lines import LineEnding, LineRecord, RecordLength, SplitLines, split_lines
from .masking import mask, mask_ach_file
from .model import AchFile, Batch, Entry, FieldValue, Record
from .parser import parse, parse_ach
from .reference import ReferenceEntry, lookup_code, reference_catalog
from .repair import RepairChange, RepairResult, repair_control_records
from .validator import FileSummary, ValidationReport, validate, validate_ach_file

__all__ = [
    "FieldSpec",
    "LineEnding",
    "LineRecord",
    "RecordLayout",
    "RecordLength",
    "SplitLines",
    "default_layouts",
    "build_record",
    "load_layouts",
    "split_lines",
    "AchFile",
    "Batch",
    "Entry",
    "FieldValue",
    "Record",
    "parse",
    "parse_ach",
    "mask",
    "mask_ach_file",
    "FileSummary",
    "ValidationReport",
    "validate",
    "validate_ach_file",
    "ReferenceEntry",
    "lookup_code",
    "reference_catalog",
    "generate_ach_file",
    "RepairChange",
    "RepairResult",
    "repair_control_records",
    "RecordDifference",
    "diff_ach_files",
]
