# Streaming Validation Parser

Status: Proposed architectural phase
Date: 2026-09-12
Owner: Core + QA

## Decision Summary

Build a validation-only parser that consumes the existing line stream once and
updates compact parser state, rule state, aggregates, and a bounded finding
buffer as records arrive. It must not build `FieldValue`, `Record`, `Entry`,
`Batch`, or snapshot tuples for the validation path. The existing tolerant
parser remains the implementation of the public parse model.

The target is plain validation of a deterministic 100,000-entry file in under
two seconds on the benchmark laptop, while keeping peak memory below 500 MB
and preserving the existing `ValidationReport` contract.

## Evidence and Current Bottleneck

The current baseline in [Performance Benchmark](performance.md) is:

```text
entries_requested=100000
records=100030
validation_seconds=5.015
peak_megabytes=270.6
```

A wall-clock-only measurement after the entry lookup optimization was `4.434s`.
The existing [validation snapshot](validation-snapshot-contract.md) avoids some
full-parser fields, but `build_validation_snapshot()` still retains every
physical line and materializes validation records, entries, addenda, and
tuples. `validation_context_from_snapshot()` then reconstructs the legacy
`AchFile` object graph so the current rules can run. The comparison recorded in
the performance document was `11.011s` for the snapshot-adapter path versus
`6.153s` for full validation in that run. This is an adapter correctness
scaffold, not a production optimization.

The dominant cost to remove is therefore object allocation and the second
traversal required by the rule-facing model, not line splitting alone. The
current parser also creates every layout field even when validation does not
read it.

## Proposed One-Pass Data Model

The new internal parser owns one mutable `StreamState` for the duration of a
validation call. Each physical line is consumed in source order and is not
retained after all rules that need it have been evaluated, except for the
bounded finding payload and the minimal control/header state needed later.

```text
StreamState
  line_count, line_ending, placement state, first/previous record facts
  header facts needed by FH rules
  current batch facts and control record facts
  current entry facts and addenda-parent facts
  trace-order/uniqueness state
  batch and file aggregate accumulators
  bounded findings grouped by deterministic rule bucket
  deferred end-of-file checks
```

Field extraction is a fixed-width slice operation driven by the layout table.
It produces only the raw/value/position facts listed in the dependency matrix;
it does not create general-purpose field objects. Current-line facts are
evaluated immediately. Batch-control checks run when a batch closes, and
file-control/end-of-stream checks run once at the end. The parser must retain
raw slices only where a finding needs `actual`, a control comparison needs a
value, or a later rule explicitly depends on the value.

The implementation may use mutable internal structs for speed. They are not a
new public parse model and must not be returned from the core or MCP APIs.

## Required Rule Inputs

The streaming implementation must cover every dependency in the existing
[snapshot contract](validation-snapshot-contract.md):

- Structure: raw content, content length, printable-ASCII status, record type,
  line number, line-ending summary, placement state, padding/control boundary,
  and physical line count.
- File and batch headers: the current fixed-width fields used by FH001-FH010
  and BH001-BH011, including raw immediate-destination and comparison slices.
- Entries: transaction code, RDFI and check digit, account/name fields,
  amount, addenda indicator, trace number, payment type, SEC context, and
  source positions.
- Addenda: type, sequence, parent trace suffix, return reason, original trace,
  change code, corrected data, parent entry, and SEC context.
- Controls: header/control comparison fields and the computed batch/file
  aggregates below.

Rule code may initially consume a small adapter view, but that view must read
the streaming state directly and must not reconstruct the complete legacy
model. Rules that require end-of-file knowledge must consume finalized state.

## Aggregate Calculations

Maintain these counters while entries and addenda arrive:

- Per batch: entry-plus-addenda count, RDFI hash modulo `10_000_000_000`,
  debit cents, and credit cents.
- Per file: batch count, entry-plus-addenda count, RDFI hash modulo
  `10_000_000_000`, debit cents, credit cents, and block count
  `(line_count + 9) // 10`.
- Per entry: parsed transaction code, amount cents, RDFI, trace number, credit
  or debit classification, prenote flag, zero-dollar flag, addenda count, and
  source positions.

Debit and credit totals must retain the existing exclusion semantics for
prenote and zero-dollar entries. Batch totals must be finalized before batch
control findings; file totals must be finalized before file control findings.
The same accumulator values must drive both expected control values and the
reported summary, eliminating independent calculation paths.

## Finding and Order Parity Contract

For the same input, options, and rule set, the streaming path must match the
current path on `valid`, severity counts, `counts_by_rule`, `truncated`, and
summary counts. Every finding must match on rule ID, severity, message,
line number, record type, position, field, expected value, and actual value.

Finding order is observable because truncation keeps the first visible
findings. Preserve the current rule-bucket order:

1. structure (`S`)
2. headers (`FH`/`BH`)
3. entries (`ED`)
4. addenda (`AD`)
5. controls (`BC`/`FC`)

Within a bucket, preserve source-line order and the current rule registry order.
The bounded buffer may retain at most the information needed to compute all
counts and the first `max_findings` findings after severity filtering. Counts
must still include findings hidden by `min_severity` and findings beyond the
visible limit, as required by [the validator contract](validation-snapshot-contract.md).

Parity must be established with the existing seeded mutation tests, at least
100 additional deterministic corpus cases, malformed ordering cases, mixed
line endings, short/overlong records, and sensitive-field fixtures before the
new path can become the default.

## Public API Compatibility

Keep `validate()` and `validate_ach_file()` signatures and return types
unchanged, including `min_severity`, `max_findings`, `rule_ids`, custom
`runners`, `ValidationReport`, `Finding`, and `FileSummary`. Keep
`parse_ach_file`/`parse` and all `AchFile`, `Record`, and `FieldValue` behavior
unchanged. The streaming path is an internal implementation selected by the
validator; it must not expose a second public parse representation or change
MCP serialization.

Custom rule runners are a compatibility boundary: the optimized path may be
used only when all requested runners are supported by the native streaming
adapter. Otherwise validation must fall back to the existing context path,
with identical results.

## Migration and Feature Flag

1. Implement the streaming engine behind an internal, test-only feature flag.
2. Run full-parser versus streaming differential tests and benchmark both paths.
3. Enable the flag for opt-in local and scheduled performance runs only.
4. Make streaming the default only after parity, security review, and the
   benchmark gate pass on the supported Python/platform matrix.
5. Retain the full-parser path as an internal rollback switch for one release
   cycle, with a diagnostic showing which path ran.

The flag must not be a new user-facing MCP option and must not spread mode
branches through the tolerant parser. A single validator dispatch point should
select the implementation.

## Benchmark Acceptance Criteria

Use `scripts/benchmark_validation.py --entries 100000` with plain wall-clock
measurement as the release gate; report Python version, platform, record count,
validity, error count, and the separate `tracemalloc` peak. Acceptance requires:

- validation wall-clock time `< 2.000s` on the agreed laptop benchmark;
- peak Python allocation `< 500 MB` in the separate memory run;
- no false-valid result and zero parity disagreements in the differential corpus;
- repeated runs documented with environment and seed, with no generation time
  included in validation time;
- no benchmark added to the ordinary unit-test/PR gate unless separately
  approved, consistent with [the performance phase plan](phase-validation-performance-and-release.md).

The result must be compared with the documented `5.015s` baseline. A faster
benchmark with changed findings, changed ordering, or omitted malformed-input
handling is a failure, not an optimization.

## Security and Privacy Constraints

Preserve the boundaries in [the threat model](threat-model.md): no network,
filesystem, MCP, telemetry, or logging responsibilities in the core parser;
input remains data, never instructions; and logs must not contain ACH content
or field values. Do not retain sensitive account or identification slices after
their rule checks complete. Findings and diagnostics must use the existing
masking policy and must not make sensitive values visible through `actual`.

Maintain tolerant handling for malformed, short, overlong, mixed-ending, and
unterminated input without raising solely because input is invalid. Keep input
size limits and allowed-root/symlink checks in the server input layer. Streaming
is not a substitute for those limits: a one-pass parser still needs bounded
finding storage and must not permit attacker-controlled unbounded state such as
all trace numbers unless a rule contract requires it.

## Rollback Plan

If parity, performance stability, memory bounds, or security review fails,
disable the internal streaming flag and route validation back to the current
full-parser implementation. Keep the parser API and report contracts intact,
preserve differential failures as triage artifacts, and do not ship a default
switch based only on a favorable synthetic benchmark. Remove the flag only
after the streaming path has completed a release cycle without regressions.

## Explicitly Out of Scope

- Changes to the public parse model, masking API, repair behavior, MCP schema,
  CLI contract, or transport boundaries.
- New SEC codes, deeper CTX/IAT validation, bank profiles, or calendar/reference
  data claims.
- ACH transmission, hosted deployment, network calls, telemetry, or external
  validation services in runtime code.
- Replacing the existing rule IDs, finding schema, severity policy, or
  deterministic ordering contract.
- Unbounded retention of complete input, every trace number, every field, or a
  second full object graph.
- CI/workflow changes, publishing, release approval, or accepting a revised
  performance target without product-owner evidence and approval.