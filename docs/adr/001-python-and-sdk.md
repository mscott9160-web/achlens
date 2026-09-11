# ADR 001: Python and MCP SDK

## Context

The project needs a supported Python runtime and an official MCP integration
path. Sprint 0 must remain usable without implementing or importing MCP.

## Decision

Use Python >=3.12,<3.14 for local scaffolding. The future MCP adapter will use
the official `mcp` package and FastMCP interface, pinned when that adapter is
implemented.

## Consequences

The package has a clear runtime range and can ship a CLI without an MCP
dependency today. CI also exercises the specified 3.11, 3.12, and 3.13 matrix;
the Python 3.11 compatibility decision must be reconciled before release.
