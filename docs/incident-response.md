# Incident Response

This runbook covers security, data-handling, release, and service-impacting
incidents involving the repository or published package.

## Ownership

The repository owner is the incident coordinator until another maintainer is
explicitly assigned in the private GitHub security advisory or incident issue.
The coordinator keeps the record, assigns technical investigation and release
tasks, and decides when stakeholders need an update. Do not add real ACH data
to the record.

## First Actions

1. Move suspected vulnerabilities to a private GitHub Security Advisory. Do
   not discuss exploit details in a public issue.
2. Preserve the smallest useful evidence: version or commit, timestamps,
   affected artifact, logs with sensitive values removed, and reproduction
   steps using synthetic data.
3. Assess whether the issue affects source, a published package, a release
   credential, repository settings, or user data. Revoke or rotate exposed
   credentials through the owning GitHub or package-registry controls.
4. Pause an affected release or mark the affected version in the advisory and
   release discussion. Do not change release workflow logic as an incident
   shortcut.

## Resolution and Closure

The coordinator records impact, scope, owner, mitigation, validation evidence,
and the decision to release, withdraw, or communicate. After remediation, run
the documented quality checks and package smoke test as applicable, publish a
GitHub advisory or release note when disclosure is appropriate, and record
follow-up actions with owners in a GitHub issue.