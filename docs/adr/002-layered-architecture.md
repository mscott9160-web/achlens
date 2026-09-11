# ADR 002: Layered Architecture

## Context

ACH domain logic, MCP protocol behavior, and command-line behavior have
different testing and reuse needs.

## Decision

Use a pure core library, a thin MCP adapter, and a thin CLI. The core must not
import the MCP SDK.

## Consequences

Core behavior can be tested independently of protocol concerns. The project
has explicit boundaries to maintain when later sprints add parser and server
features.
