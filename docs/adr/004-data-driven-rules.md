# ADR 004: Data-Driven Validation Rules

## Context

The rule catalog must serve both as an implementation manifest and as user
documentation, while each rule still needs executable behavior.

## Decision

Store rule metadata in `rules.yaml` and implement each rule with a dedicated
function or module when validation begins.

## Consequences

The catalog can support parity checks, generated documentation, and targeted
tests. The catalog and rule implementations are intentionally deferred beyond
Sprint 0.
