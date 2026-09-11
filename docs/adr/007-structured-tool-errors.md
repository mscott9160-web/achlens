# ADR 007: Structured Tool Errors

## Context

An MCP client needs actionable failure information that an assistant can
explain without an unhandled protocol exception.

## Decision

Future tools will return structured error objects with stable error codes,
messages, and hints instead of raising errors to the client.

## Consequences

Callers can handle failures consistently and tests can assert error contracts.
The error schema remains unimplemented until the MCP tool sprint.
