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

Signed release policy is documented in
[Release Signing Policy](release-signing.md). Signed-tag enforcement is not
active until the owner completes the key, protection, and rehearsal steps in
that policy. Tradeoffs for SSH, GPG, Sigstore, backup ownership, and support
commitments are summarized in
[Governance Decision Options](governance-decision-options.md).

Performance verification for the documented 100,000-entry target passed. The
streaming suite recorded 193 passed and 1 skipped; hosted Windows, Ubuntu, and
macOS runs each completed in under one second, used 53.8 MB, produced valid
reports with no errors, and matched the legacy path exactly. Optimized
streaming is enabled by default for built-in runners, while
`ACHLENS_DISABLE_STREAMING_VALIDATION=1` remains an internal rollback switch.
