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
