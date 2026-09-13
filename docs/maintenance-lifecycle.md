# Support And Maintenance Lifecycle

For `v0.1.x`, the project uses the conservative best-effort support policy:
there is no response-time SLA or guaranteed fix date. Formal support windows
will be reconsidered after a second active maintainer and meaningful support
volume exist.

This policy describes the support boundary for `achlens`. It is maintained
through the repository and does not create a guaranteed service level, paid
support channel, or promise of a response or fix by a particular date.

## Supported Versions

- **Python:** Python 3.11, 3.12, and 3.13 are supported. This follows the
  package requirement of `>=3.11,<3.14` in `pyproject.toml`.
- **Package:** Version `0.1.2` is the current maintained package release. The
  declared package version and dependency bounds in `pyproject.toml` are
  authoritative; older release lines are not supported unless explicitly
  documented otherwise.
- **Operating systems:** The project supports environments covered by the
  regular test and release checks. Platform-specific behavior may vary.

Users should report the installed `achlens` version, Python version, operating
system, and a minimal synthetic reproduction when requesting support. Versions
outside the ranges above may still work, but are not part of the supported
compatibility target.

## Support And Security

Use the [support process](support.md) for setup, usage, documentation, and
reproducible defect questions. Report suspected vulnerabilities privately
through the channel documented in [SECURITY.md](../SECURITY.md), not through a
public issue.

Security reports receive priority according to severity, reproducibility,
exposure, and maintainer availability. The project will investigate, coordinate
a fix or mitigation when appropriate, and communicate through the available
repository security process. No response or remediation deadline is promised.

## Deprecation

When a public command, API, input, output, or supported environment is planned
for removal or incompatibility, maintainers should:

1. document the change and its user impact;
2. name a replacement or explain that none is available; and
3. state the intended removal or support-boundary change in the release notes
   and relevant documentation.

The project will provide a transition period when practical. Urgent security,
upstream, or maintenance constraints may shorten that period; the reason and
available mitigation should be recorded. A deprecation is complete when the
replacement guidance and release documentation are published and the obsolete
surface is removed or excluded from the supported target.

## Issue Triage

The repository owner owns initial triage. Maintainers review open support,
bug, and maintenance issues at least weekly when the project is active. Triage
records severity, reproducibility, owner, and disposition; duplicates and
issues without enough information may be closed with an explanation.

Security reports and active release or incident risks are handled outside the
public issue cadence through the processes linked above. Response times vary
with severity, reproducibility, maintainer availability, and project
priorities.

## End Of Support

Support for a Python version, package release line, or platform ends when it is
outside the declared compatibility target, is superseded by a documented
release line, or can no longer be maintained and tested reliably. The change
should be recorded in release notes and the relevant support documentation.

The project may also enter maintenance-only or end-of-support status if there
are no active maintainers, required upstream dependencies are unavailable, or
the project is intentionally retired. In those cases, the repository should
state the boundary clearly and preserve any available migration or archival
guidance. End of support does not guarantee that old releases stop working; it
means new fixes and support requests are no longer part of the maintained
commitment.