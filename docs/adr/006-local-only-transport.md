# ADR 006: Local-Only Stdio Transport

## Context

The product is intended for local ACH inspection and must not make outbound
network calls or send telemetry.

## Decision

Use local execution and stdio transport for the future MCP server, with no
network calls or telemetry.

## Consequences

The trust boundary is smaller and sensitive files remain local. Network and
transport enforcement will be added with the MCP server and security work.
