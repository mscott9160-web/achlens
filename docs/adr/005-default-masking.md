# ADR 005: Default Sensitive-Field Masking

## Context

ACH content can contain sensitive payment information, and tool output may be
placed into an LLM context.

## Decision

Mask sensitive fields by default. A future server operator setting may enable
reveal behavior, subject to the specification's controls.

## Consequences

Default outputs reduce unnecessary exposure of sensitive values. Masking rules,
configuration, and tests must be implemented before any file-reading tools are
released.
