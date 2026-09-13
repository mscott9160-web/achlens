# Release Signing Policy

## Status

SSH-signed tags are selected for the next release, but enforcement is **not
active yet**. No release should claim signed-tag verification until the
repository owner completes key setup and the rehearsal evidence below.

## Authority

The repository owner is the release-signing authority and must approve the
primary signing key and one recovery signer before enabling enforcement. A
release tag must use the `vMAJOR.MINOR.PATCH` format and point to the reviewed
release commit.

The signing key must remain on an operator-controlled device or approved
hardware-backed credential. It must not be stored in GitHub Actions secrets,
the repository, package artifacts, or issue comments. The public key or
fingerprint may be recorded in the private maintainer inventory and in the
release approval record.

## Rotation And Revocation

Rotate the signing key when an owner leaves, the credential is suspected to be
exposed, the recovery signer changes, or the owner-approved rotation interval
expires. On suspected compromise:

1. Stop release publication immediately.
2. Revoke the affected key and record the incident privately.
3. Generate and verify a replacement key with the recovery signer.
4. Update the maintainer inventory and repository protection settings.
5. Rebuild only from a reviewed commit and publish a corrective release note
   when appropriate.

Never rewrite or force-update an existing release tag to repair a signature.
Create a new patch release instead.

## Verification And Enforcement

Before enabling enforcement, the release owner must demonstrate locally and in
CI that:

- A valid signed tag points to the reviewed commit.
- The signer fingerprint is trusted by the release procedure.
- An unsigned tag is rejected before package build or publication.
- A tag pointing to an unreviewed commit is rejected.
- The `pypi` environment approval remains required.
- The GitHub release, PyPI artifact, and Registry metadata all refer to the
  same signed tag and version.

The release workflow must verify the tag before the build and publish jobs can
run. Until that workflow check exists, signed-tag status remains a manual
release approval gate.

## Recovery Evidence

Every signed release approval should record:

- Version and tag name.
- Reviewed commit SHA.
- Signer identity and public-key fingerprint.
- Verification command and result.
- Product, security, and release approvers.
- Any accepted unresolved risk.

Do not put private keys, recovery codes, or real ACH data in the record.
