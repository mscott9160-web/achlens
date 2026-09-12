# Threat Model

This document records the current v1 security boundary for `achlens`.

## Assets

- Account numbers and individual identification numbers in parsed records.
- NOC corrected data, which may contain replacement account information.
- Local ACH files supplied through MCP path inputs.
- Repaired output files written by the repair tool.

## Trust Boundaries

1. An MCP client supplies content or a local path.
2. The server input layer resolves and size-checks that input.
3. The pure core parser and validator process the text.
4. The adapter serializes structured results back to the MCP client.

File content is data, not instructions. Free-text ACH fields must not become
tool instructions or prose guidance.

## Controls

- No runtime network or telemetry calls.
- MCP path mode requires `ACHLENS_ALLOWED_ROOTS`.
- Paths are resolved before root containment checks, including symlink targets.
- Directories and oversized files are rejected.
- Sensitive fields are masked by default in structured parsed output.
- Path-mode repair creates a new file and refuses overwrite.
- Path-mode repair does not return repaired content to the MCP client.
- Tool failures use structured error codes rather than raw exceptions.
- Logs must use stderr and must not contain file content or field values.

## Residual Risks

- An operator can explicitly enable sensitive-field reveal with
  `ACHLENS_ALLOW_REVEAL=1`; this is an operator-controlled local setting.
- CLI users have direct filesystem authority and are responsible for the paths
  they provide.
- Reference rows marked `UNVERIFIED` must not be presented as authoritative
  Nacha guidance.
- Full no-network socket enforcement, dependency auditing, and differential
  validation against moov-io/ach remain release-hardening work.

## Release Checklist

- Run `ruff check .` and `ruff format --check .`.
- Run `mypy --strict src`.
- Run the full pytest suite, including masking and path-boundary tests.
- Run `pip-audit` in CI.
- Review all reference rows and resolve or explicitly approve `UNVERIFIED`
  status before release.