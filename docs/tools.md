# MCP Tools

Achlens is a stdio MCP server for synthetic ACH-file development. It never
transmits file content. Send ACH text through a `content` argument by default.
Path arguments are rejected unless the local operator configures
`ACHLENS_ALLOWED_ROOTS`; see [SECURITY.md](../SECURITY.md).

Sensitive account and identification data is masked. `reveal_sensitive` is not
an override for validation or summary results. Do not send real payment data.

## Tools

| Tool | Purpose | Key inputs |
| --- | --- | --- |
| `server_status` | Confirm that the local stdio server is ready. | None |
| `validate_ach_file` | Validate structure and control totals. | Exactly one of `content` or `path`; optional `min_severity` (`error`, `warning`, or `info`) and `rule_ids`. |
| `summarize_ach_file` | Summarize batches, totals, SEC codes, returns, and NOCs. | Exactly one of `content` or `path`. |
| `parse_ach_file` | Return a bounded page of named record fields. | Exactly one of `content` or `path`; optional `offset`, `limit` (1-500), and `record_types`. |
| `explain_control_totals` | Compare stated and recomputed file or batch control totals. | Exactly one of `content` or `path`; optional `batch_number`. |
| `check_routing_number` | Check an ABA routing-number check digit. | `routing_number`. |
| `lookup_ach_code` | Look up a return, NOC, transaction, SEC, or service-class code. | `kind`, `code`. |
| `generate_test_ach_file` | Generate a deterministic, balanced synthetic file. | Optional `sec_code`, `entries_per_batch`, `batches`, `service_class`, and `seed`. |
| `repair_control_records_tool` | Repair derived controls. | Exactly one of `content` or `path`; optional `restore_trailing_spaces`. |
| `diff_ach_files_tool` | Compare two ACH contents with masked field-level differences. | `left_content`, `right_content`. |

Validation-oriented tools return structured data. Invalid inputs return an
`error` object with a stable code, message, and remediation hint.

## Resources

- `ach://layouts` - packaged ACH record layouts.
- `ach://rules` - packaged validation rule catalog.
- `ach://reference/{kind}` - packaged reference-code table for a supported
  reference kind.

## Prompts

- `debug_ach_file` - a deterministic validation and control-total debugging
  flow.
- `explain_returns` - a concise return and NOC explanation flow.

## Repair behavior

Content-mode repair returns repaired content. Path-mode repair only writes a new
sibling file ending in `.repaired`; it refuses to overwrite an existing file
and does not return the repaired content.
