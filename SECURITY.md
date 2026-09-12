# Security

`achlens` is local-first software for inspecting synthetic ACH files. It does
not transmit files, connect to banks, or make outbound network calls as part of
its runtime tools.

## Data Rules

- Never report or commit real payment data, account numbers, routing/account
  pairs, or real ACH files.
- Use generated fixtures and the synthetic generator for tests and examples.
- Sensitive parsed fields are masked by default: account numbers, individual
  identification numbers, and NOC corrected data expose only a masked value
  with the final four characters preserved.
- Reveal behavior is disabled unless `ACHLENS_ALLOW_REVEAL=1` is explicitly
	configured by the local operator.

## File Access

MCP path inputs are disabled unless `ACHLENS_ALLOWED_ROOTS` is configured.
Configured paths are resolved before checking containment, so `..` traversal
and symlink escapes are rejected. Directories, missing paths, non-UTF-8 files,
and files above `ACHLENS_MAX_BYTES` are rejected.

The CLI accepts explicit local paths because it is a user-run command-line
program. MCP path access remains subject to the allowlist.

## Writes

Only the repair tool writes files. Path-mode repair writes a new sibling file
with a `.repaired` suffix and refuses to overwrite an existing output. It does
not return repaired file content in path mode.

## Reporting

Report suspected vulnerabilities privately through the repository's GitHub
security channel. Do not include real ACH content in an issue, pull request,
log, or test fixture.
