# Release

Releases are tag-driven. The workflow in `.github/workflows/release.yml` runs
when a tag matching `v*` is pushed.

Before the first release, configure PyPI trusted publishing for:

- GitHub owner: `mscott9160-web`
- Repository: `achlens`
- Workflow: `release.yml`
- Environment: `pypi`
- Package: `achlens`

The workflow builds with `uv`, checks distribution metadata, publishes through
PyPI's OIDC trusted-publishing action, and creates a GitHub release with
 generated notes. It does not contain a long-lived PyPI token.

Do not create a release until the project name, Nacha verification, reference
status policy, and release quality gates have been accepted by the product
owner.

## Approval Ownership

The repository owner is the release approver and is responsible for confirming
the product-owner acceptance above before a release tag is pushed. Maintainers
may prepare a release candidate and evidence, but they must not treat a green
CI run as product or compliance approval.

Record the approval in the release pull request or GitHub release discussion,
including the version, quality-check result, unresolved-risk decision, and the
approver's GitHub account. Configure required reviewers for the `pypi`
environment in repository settings before enabling the first production
release. This documentation does not itself grant permissions or change the
release workflow.

Dependency review is part of release approval. Follow
[Dependency Governance](dependency-governance.md) for lockfile checks,
`pip-audit` exceptions, ownership, and expiry requirements.

Performance approval is also required for the documented 100,000-entry target.
The current measured result remains above two seconds, so a release approver
must either provide evidence that the target has been met or record an explicit
decision accepting the revised performance risk. Snapshot-adapter results do
not satisfy this gate while that path remains slower than full validation.
