# ADR 008: Tolerant Parsing and Strict Validation

## Context

Broken ACH files need useful diagnostics for all discoverable problems rather
than stopping at the first malformed record.

## Decision

The future parser will recover as much structure as possible, while the
validator will apply strict rules and report findings.

## Consequences

Users get broader diagnostics from malformed input, at the cost of more
explicit parser recovery behavior and validation tests. Both components are
deferred beyond Sprint 0.
