# ADR 003: Data-Driven Record Layouts

## Context

ACH records have fixed-width fields that must be shared by parsing, building,
documentation, and tests.

## Decision

Represent record layouts as data in `ach_layouts.yaml`, rather than encoding
field positions directly in Python logic.

## Consequences

One layout definition can drive multiple features and reduce duplicated
position logic. Layout verification is deferred to CORE-01 and no layout data
is included in Sprint 0.
