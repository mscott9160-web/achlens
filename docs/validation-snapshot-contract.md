# Validation Snapshot Contract

Status: VPR-01 design
Date: 2026-09-12

## Purpose

The validation snapshot is an internal representation for the optimized
validator path. It is not an MCP response and does not replace `AchFile`,
`Record`, or `FieldValue` in the public parse API.

The full tolerant parser remains responsible for `parse_ach_file`, summaries,
masking, repair, and field-level inspection. The snapshot exists to avoid
materializing every named field when validation only needs a bounded subset.

## Invariants

- Every physical source line remains represented by line number, raw content,
  record type, length status, and line-ending metadata.
- Field slices retain their original 1-based start and end positions.
- Numeric values are typed only when the complete slice is numeric.
- Blank fields remain distinguishable from malformed fields.
- Unknown and misplaced records remain visible to structural rules.
- Batch and file aggregates are computed from the same entry stream used by
  control-total rules.
- Sensitive values are not rendered by the snapshot itself.
- The snapshot has no MCP, filesystem, network, or logging responsibilities.

## Proposed Internal Shapes

The implementation may use dataclasses or equivalent private types, but the
following information must be available:

```text
ValidationSnapshot
  lines: tuple[ValidationLine, ...]
  line_count: int
  line_ending: LF | CRLF | mixed | none
  header: ValidationRecord | None
  batches: tuple[ValidationBatch, ...]
  file_control: ValidationRecord | None
  padding: tuple[ValidationLine, ...]
  unparsed: tuple[ValidationLine, ...]
  file_aggregates: FileAggregates

ValidationLine
  line_number: int
  raw: str
  content: str
  record_type: known code | padding | unknown
  length: exact | short | overlong
  potential_trailing_space_loss: bool

ValidationRecord
  line: ValidationLine
  layout: layout name | unknown
  fields: mapping[str, ValidationField]

ValidationField
  name: str
  start: int
  end: int
  raw: str
  value: str | int | None

ValidationEntry
  detail: ValidationRecord
  addenda: tuple[ValidationRecord, ...]
  entry_aggregates: EntryAggregates

ValidationBatch
  header: ValidationRecord | None
  entries: tuple[ValidationEntry, ...]
  control: ValidationRecord | None
  aggregates: BatchAggregates

FileAggregates
  batch_count
  entry_addenda_count
  entry_hash
  total_debit_cents
  total_credit_cents
  block_count

BatchAggregates
  entry_addenda_count
  entry_hash
  total_debit_cents
  total_credit_cents

EntryAggregates
  transaction_code: int | None
  amount_cents: int | None
  receiving_dfi: int | None
  trace_number: str
  is_credit: bool | None
  is_debit: bool | None
  is_prenote: bool
  is_zero_dollar: bool
```

## Required Field Map

### Structure

The structure rules use the line stream, not parsed fields:

- raw content and content length
- printable ASCII status
- first-character record type
- line number
- line ending summary
- file-control/padding boundary
- physical line count

### File Header

```text
record_type_code
priority_code
immediate_destination
immediate_origin
file_creation_date
file_creation_time
file_id_modifier
record_size
blocking_factor
format_code
```

Immediate destination also needs the raw fixed-width slice so the blank-prefix
convention and routing check can be distinguished.

### Batch Header

```text
service_class_code
company_name
company_identification
standard_entry_class_code
company_entry_description
effective_entry_date
settlement_date
originator_status_code
originating_dfi_identification
batch_number
```

### Entry Detail

```text
transaction_code
receiving_dfi_identification
check_digit
dfi_account_number
amount
individual_name
receiving_company_name
addenda_record_indicator
trace_number
payment_type_code
```

The selected layout determines whether `individual_name` or
`receiving_company_name` applies.

### Addenda

```text
addenda_type_code
addenda_sequence_number
entry_detail_sequence_number
return_reason_code
original_entry_trace_number
change_code
corrected_data
```

### Batch Control

```text
service_class_code
entry_addenda_count
entry_hash
total_debit_entry_dollar_amount
total_credit_entry_dollar_amount
company_identification
message_authentication_code
reserved
originating_dfi_identification
batch_number
```

### File Control

```text
batch_count
block_count
entry_addenda_count
entry_hash
total_debit_entry_dollar_amount
total_credit_entry_dollar_amount
reserved
```

## Rule-to-Dependency Matrix

| Rule group | Snapshot dependency |
|---|---|
| S001-S003 | line length, ASCII status, record type |
| S004-S014 | line stream, placement state, padding boundary, line count |
| FH001-FH010 | file-header field map |
| BH001-BH011 | batch-header field map and batch order |
| ED001-ED011 | entry field map and entry aggregates |
| ED012-ED014 | per-batch/file trace state and ODFI |
| ED015-ED016 | WEB payment field, transaction code, SEC |
| AD001-AD008 | parent entry, addenda field map, SEC context |
| BC001-BC009 | batch header/control fields and batch aggregates |
| FC001-FC007 | file control fields and file aggregates |

## Parity Acceptance

For every fixture in the existing test suite, the following must agree between
full-parser validation and snapshot validation:

- `valid`
- severity counts
- counts by rule
- rule IDs
- line numbers
- record types
- field positions
- expected and actual values
- truncation behavior at the validator boundary

The first implementation should run both paths behind tests. Switching the
normal validator to the snapshot path requires parity tests to pass for the
full existing corpus.
