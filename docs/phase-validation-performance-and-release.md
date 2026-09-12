# Phase: Validation Performance and Release Readiness

Status: Planned
Owner: Scrum Master / PO proxy
Baseline commit: `834b479`
Date: 2026-09-12

## Goal

Reduce validation cost for a 100,000-entry synthetic ACH file while preserving
all existing findings and public parser behavior, then close the remaining
release gates without publishing unverified Nacha or reference-data claims.

## Current Baseline

Measured with `python scripts/benchmark_validation.py --entries 100000`:

```text
records=100030
validation_seconds=5.015
peak_megabytes=270.6
valid=True
error_count=0
```

Target from the product specification:

- validation under 2 seconds on a laptop
- memory under 500 MB
- zero false-valid results in the differential corpus

The memory target currently passes. The wall-clock target does not.

## Scope

### In Scope

- A validation-only representation that avoids materializing every parsed
  `FieldValue` when the caller only needs validation.
- One-pass extraction of fields required by structure, header, entry, addenda,
  and control rules.
- Reuse of calculator aggregates for counts, hashes, totals, traces, and block
  information.
- Behavioral parity tests between full parsing plus validation and the
  validation-only path.
- Differential-test harness design and triage documentation.
- Performance measurement and CI reporting.
- Final release-readiness checklist.

### Out of Scope

- Changes to the public `parse_ach_file` field-level output contract.
- New SEC codes, CTX deep validation, IAT support, bank profiles, or calendars.
- Network calls, hosted deployment, or ACH transmission.
- Guessing unresolved Nacha or return/NOC reference data.
- Publishing a package or MCP Registry entry before PO approval.

## Architecture Decision

Add a dedicated validation path rather than adding mode flags throughout the
existing tolerant parser.

```text
raw text
  -> line splitter
  -> validation parser
       - record type and length facts
       - only rule-required fixed-width slices
       - streaming aggregates
  -> existing rule context adapter
  -> existing Finding and ValidationReport contracts
```

The full parser remains the source for `parse_ach_file`, masking, summaries,
and repair. The validation parser is an internal optimization and must not
expose a second incompatible public parse model.

## Work Packages

### VPR-01: Validation Snapshot Contract

Owner: Architect + Core Dev

Define a small internal model containing:

- physical line facts and line-ending summary
- record type and placement state
- batch and entry relationships needed by rules
- raw slices for fields used by rules
- precomputed entry/addenda counts
- RDFI hash addends and batch/file hashes
- debit/credit totals
- trace ordering and uniqueness facts

Acceptance criteria:

- No MCP imports or filesystem access.
- Public `AchFile`, `Record`, and `Finding` models remain unchanged.
- A short design note identifies which current rule reads map to each snapshot
  field.

### VPR-02: Streaming Validation Parser

Owner: Core Dev

Implement a single-pass parser over `split_lines()`.

Acceptance criteria:

- Handles LF, CRLF, mixed endings, unterminated final lines, short lines, and
  overlong lines with the existing structural semantics.
- Does not allocate a `FieldValue` for fields unused by validation.
- Preserves enough raw slices to produce current field positions and
  expected/actual control findings.
- Invalid structure remains reportable rather than raising.
- Existing full parser behavior is unchanged.

### VPR-03: Rule Context Adapter

Owner: Core Dev + Architect

Adapt existing S/FH/BH/ED/AD/BC/FC rules to consume the snapshot or an adapter
with the current rule-facing interface.

Acceptance criteria:

- Existing 144-test suite remains green.
- Every current rule ID can execute through the optimized validator path.
- Findings match the full-parser path by rule ID, severity, line, field,
  position, expected, and actual values.
- Rule ordering is deterministic.

### VPR-04: Differential Behavior Tests

Owner: QA

Generate a corpus from seeded valid files and supported mutations:

- valid PPD, CCD, and WEB files
- multiple batches and addenda
- S001/S011/ED004/ED007/ED012/AD004 mutations
- BC/FC derived-field mutations
- malformed and shuffled records
- sensitive-field fixtures

Acceptance criteria:

- Full-parser validation and validation-only validation agree on `valid`,
  counts, rule IDs, and finding locations.
- At least 100 seeded corpus cases run locally.
- Any disagreement is triaged in `docs/differential-triage.md`.

### VPR-05: Performance Gate

Owner: QA + Core Dev

Extend `scripts/benchmark_validation.py` with:

- plain validation wall-clock time
- optional tracemalloc memory measurement
- Python version and platform output
- nonzero exit status when an explicit threshold is supplied and exceeded

Acceptance criteria:

- Baseline remains reproducible with `--entries 100000`.
- Benchmark does not run in the ordinary unit-test job.
- CI or a scheduled workflow can run it without changing the normal PR gate.
- The report distinguishes measured wall-clock time from instrumentation time.

### VPR-06: Differential Harness

Owner: QA + Security Reviewer

Add an opt-in differential workflow that can run moov-io/ach in Docker when
available. Do not make external Docker availability a required local test.

Acceptance criteria:

- No network call is made by the achlens runtime itself.
- Generated and mutated fixtures are synthetic only.
- Validity disagreements produce an artifact and a triage entry.
- The workflow is clearly marked optional/nightly until its external endpoint
  and version are verified.

### REL-01: Release Gates

Owner: Scrum Master + PO + Docs/Security

Close the non-code blockers:

- Nacha source verification and discrepancy approval
- Return/NOC reference-data approval
- Final package/repository name decision
- PyPI trusted-publishing configuration
- Current MCP Registry schema and publisher process
- Threat-model/security review sign-off
- Dependency audit and no-network CI enforcement

Acceptance criteria:

- No `UNVERIFIED` row is presented as authoritative guidance.
- Release workflow is tested without publishing a release artifact
  accidentally.
- The PO explicitly accepts the release checklist.

## Team Handoffs

| Handoff | Producer | Consumer | Required artifact |
|---|---|---|---|
| Snapshot contract | Architect/Core Dev | Core Dev/QA | Design note and field map |
| Validation parser | Core Dev | Rule owners | Snapshot adapter and parity tests |
| Behavior corpus | QA | Core Dev | Seeded corpus and disagreement report |
| Benchmark | QA/Core Dev | Scrum Master/PO | Timing and memory report |
| Reference review | Docs/DevRel | PO/Security | Source/status review table |
| Release setup | Docs/Security | PO | Trusted-publishing and registry checklist |

## Definition of Done

- `ruff check .` passes.
- `ruff format --check .` passes.
- `mypy --strict src` passes.
- Full pytest suite passes.
- Existing MCP and CLI contracts remain compatible.
- Performance comparison is recorded against the baseline.
- Differential disagreements are triaged.
- Security and reference-data status is explicit.
- Changes are committed in focused checkpoints and pushed to GitHub.

## Risks and Decisions

| Risk | Mitigation | Decision owner |
|---|---|---|
| Snapshot diverges from tolerant parser semantics | Differential parity corpus before switching default path | Architect/QA |
| Optimization changes finding order | Stable rule-bucket ordering tests | Core Dev |
| Memory savings add complexity | Keep full parser public and isolate snapshot internally | Architect |
| moov-io endpoint/version changes | Optional workflow plus triage artifact | QA |
| Unverified code descriptions ship accidentally | Explicit status in every response/resource | PO/Security |
| Registry schema changes | Verify current official schema immediately before release | Docs/DevRel |

## Immediate Next Actions

1. Architect writes the VPR-01 snapshot field map.
2. Core Dev adds a parser-path feature flag used only by tests.
3. QA creates the 100-case parity corpus.
4. Run the optimized benchmark against the existing `5.015s` baseline.
5. Scrum Master reports whether the target is met, partially met, or requires
   scope/target review before further optimization.
