# Governance Decision Options

This record supports issue #3 and the next release approval. It separates
controls already active from decisions that require an owner or product
approval.

## Signing Tags

### Option A: SSH-signed tags

Use a dedicated SSH signing key, register the public key with GitHub, and sign
release tags with `git tag -s --format=ssh` or the equivalent Git configuration.

**Advantages**

- Uses a modern key format and the existing Git/GitHub trust model.
- Straightforward for a single release operator.
- No private key belongs in GitHub Actions.

**Costs**

- The release operator must protect and back up the private key.
- CI must verify the signature or GitHub protection must enforce it.
- Recovery requires changing the trusted signing key.

### Option B: GPG-signed tags

Use a dedicated GPG signing key, publish its fingerprint, and sign tags with
GPG. Keep the private key offline or on hardware-backed storage.

**Advantages**

- Mature GitHub verified-signature workflow.
- Familiar tooling and strong local verification support.

**Costs**

- More key-management complexity than SSH.
- Revocation and recovery require careful GPG administration.
- CI verification needs the trusted public key or GitHub verification result.

### Option C: Keyless Sigstore provenance

Use a short-lived OIDC identity and Sigstore attestations from the release
workflow instead of treating a long-lived tag-signing key as the primary trust
anchor.

**Advantages**

- Avoids long-lived signing-key storage in CI.
- Strong, auditable workflow identity and provenance.
- Good long-term supply-chain posture.

**Costs**

- More release-workflow and verifier integration work.
- Does not by itself make a Git tag appear as a traditional signed Git tag.
- Requires documenting the accepted provenance verifier.

**Recommendation:** Choose Option A for the next release if the owner wants a
small operational step. Choose Option C when provenance automation is a
priority and the team accepts the larger implementation scope. Do not enable
cryptographic enforcement until the chosen verifier has passed both signed and
unsigned rehearsal cases.

**Selected decision:** Option A, SSH-signed tags, is selected for the next
release. The signing authority, recovery signer, public-key registration, and
signed/unsigned rehearsal are still required before enforcement is activated.

## Backup Ownership

### Option A: One named trusted collaborator

Assign one maintainer as backup for security, incidents, releases, dependencies,
Registry publication, and support.

**Advantages:** simple accountability and fast escalation.  
**Cost:** creates concentration risk if that collaborator becomes unavailable.

### Option B: A GitHub team

Create a maintainer/security team and use team membership for CODEOWNERS,
release approvals, and incident escalation.

**Advantages:** shared coverage and easier rotation.  
**Cost:** requires organization/team administration and periodic membership
review.

### Option C: Staged ownership

Use one named primary and one named backup now, then migrate to a GitHub team
when a second maintainer is active.

**Recommendation:** Choose Option C immediately. Do not invent or assign a
backup without that person’s explicit consent.

**Selected decision:** Option C, staged ownership, is selected. The current
repository owner remains the primary owner; no backup maintainer is assigned
until a real person explicitly consents.

## Support Lifecycle Approval

### Option A: Conservative maintenance promise

Support the current Python range and latest patch release; provide best-effort
triage; provide security fixes while the project is maintained; deprecate with
an issue and release note.

**Advantages:** matches the current solo-maintainer reality and avoids a false
SLA.  
**Cost:** users receive no guaranteed response time.

### Option B: Formal support window

Define a fixed support window for each release line and response targets by
severity.

**Advantages:** clearer expectations for adopters.  
**Costs:** creates an operational commitment and requires backup staffing.

**Recommendation:** Approve Option A for v0.1.x. Revisit Option B after a
second active maintainer and observed support volume exist.

**Selected decision:** Option A, conservative best-effort support, is approved
for `v0.1.x`. No response-time SLA is promised. Revisit formal support windows
after a second active maintainer and meaningful support volume exist.

## Decision Record Template

Record the following in issue #3 or the next release pull request:

- Signing option: A, B, or C
- Signing authority and recovery signer
- Backup ownership option and named owners
- Support lifecycle option
- Approval account and date
- Rehearsal evidence links
- Unresolved risks and expiry dates
