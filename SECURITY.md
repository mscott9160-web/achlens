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
Security Advisories page: use **Report a vulnerability** under the repository's
Security tab. Do not open a public issue or pull request for a suspected
vulnerability.

Include the affected version or commit, the smallest safe reproduction, impact,
and any suggested mitigation. Redact credentials, payment data, account
numbers, routing/account pairs, and real ACH files. If a report cannot be
submitted through GitHub Security Advisories, open a private GitHub support
request for repository access rather than disclosing the issue publicly.

The repository owner triages reports, coordinates remediation with maintainers,
and decides when a public advisory or release note is appropriate. The project
does not promise a fixed response or resolution time; acknowledgement and
status updates depend on severity and maintainer availability.

Dependency maintenance, lockfile updates, and time-limited `pip-audit`
exceptions are governed in [docs/dependency-governance.md](docs/dependency-governance.md).
