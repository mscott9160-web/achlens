# Dependency Governance

Dependabot checks Python dependencies and GitHub Actions monthly. Updates are
grouped into reviewable pull requests and are owned by the repository owner;
maintainers may prepare the review, but the owner approves dependency changes.

## Lockfile Updates

Python dependency changes must update `pyproject.toml` and `uv.lock` together.
Use `uv lock` locally, review the resulting dependency and transitive changes,
and run the normal quality checks. Release CI runs `uv lock --check`, so a
release cannot proceed with a stale lockfile.

Do not edit `uv.lock` by hand. Dependabot pull requests must be reviewed for
both the declared requirement and the resolved versions before merging.

## Audit Exceptions

CI already runs `uv run pip-audit` through the development dependency group.
It audits the resolved Python environment only; it does not audit GitHub
Actions, source code, or vulnerabilities that are not yet represented in the
lockfile. Dependabot reviews and normal code review cover those gaps.

An accepted `pip-audit` exception must be recorded in the relevant pull
request or security review with the advisory ID, affected package and version,
reason, mitigation, owner, and an expiry date. Exceptions are temporary risk
acceptances, not permanent suppressions, and must be revisited before expiry.

## Releases

Release approval includes reviewing open dependency updates, confirming that
`pip-audit` is clean or that every exception is documented and unexpired, and
recording any accepted residual risk in the release pull request or GitHub
release discussion. The tag-driven release workflow remains the final check;
Dependabot does not publish releases or change runtime dependency versions by
itself.