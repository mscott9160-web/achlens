# Team Stories

## Sprint Goal

Stabilize `achlens` v0.1.2 in production, protect the release process, and
turn the validated streaming path into a maintainable team-owned system.

The release baseline is `v0.1.2` at commit `41edef4`. The optimized streaming
validator is enabled by default for built-in runners. The internal rollback
switch is `ACHLENS_DISABLE_STREAMING_VALIDATION=1`.

## Current Status

### Done

- **QA-02:** Windows 3.11/3.12/3.13 was added to regular CI and hosted CI
  passed.
- **SEC-03:** Structured sensitive-output masking and regression coverage were
  completed, including the NOC trace leak fix.
- **QA-01:** Optional 100-case differential validation and disagreement
  artifacts were added.
- **OPS-01:** `master` now requires pull requests, CODEOWNERS review, all nine
  quality checks, conversation resolution, and administrator enforcement. The
  `pypi` environment requires repository-owner approval and protected branches.
- **OPS-02:** GitHub Security Advisories and private vulnerability reporting are
  enabled; Dependabot alerts and security updates are enabled.

### Partial

- **OPS-03:** The v0.1.2 rollback path, scheduled benchmark, support channel,
  and issue intake exist. The required release-cycle triage log is not yet
  complete.
- **SEC-01:** `v*` tags are protected and SSH signing is selected. Key creation,
  recovery signer, cryptographic verification, and signed/unsigned rehearsal
  remain open.
- **SEC-02:** The full-suite Python socket-denial fixture is active. DNS,
  subprocess-network, and CI failure-artifact coverage remain to be proven.
- **SEC-04:** Version consistency checks and manual Registry publication are
  documented and tested. Automated Registry publication and release artifacts
  remain open.
- **SUP-02:** Staged ownership is selected and the repository owner is primary.
  No backup owner has consented yet.
- **QA-03:** Cross-platform benchmark automation and evidence are complete.
  Ongoing release-cycle review remains.

### Open

Decision options and recommendations are recorded in
`docs/governance-decision-options.md`.

- **SUP-01:** Incident-response rehearsal completed with the synthetic record
  in `docs/incident-rehearsal-2026-09-13.md`. Repeat after a second maintainer
  accepts incident backup ownership.
- **QA-04:** The review register is published in
  `docs/reference-data-review.md`. Product-owner decisions for each
  `UNVERIFIED` row remain open; no authoritative interpretation is claimed.
- **PROD-01:** Custom-runner compatibility decision remains open.
- **PROD-02:** Further optimization is deferred until measured regression or a
  new profile justifies it.

### Approved Policy

- **SUP-03:** Conservative best-effort support is approved for `v0.1.x`.
  `docs/maintenance-lifecycle.md` is the governing policy; no formal SLA is
  promised.

## Definition Of Done

Every story must have:

- Focused tests for the changed behavior.
- Full `pytest` results recorded in the pull request.
- Ruff and strict mypy passing.
- `pip-audit` and `uv lock --check` passing when dependencies are involved.
- No real ACH data in fixtures, logs, issues, or documentation.
- Documentation updated when an operator, contributor, or user workflow changes.
- Review by the owner named in the story.

## Epic A: Release Operations

### OPS-01: Configure Repository Protection

**Priority:** P0  
**Owner:** Repository owner  
**Depends on:** None

Configure GitHub branch and tag protection for `master` and release tags.
Require pull requests, passing CI, and CODEOWNERS review. Configure required
review for the `pypi` environment.

**Acceptance criteria**

- Direct pushes to `master` are restricted.
- Pull requests require the CI workflow to pass.
- CODEOWNERS review is required for owned paths.
- Release tags cannot be moved or deleted by ordinary contributors.
- The `pypi` environment requires an explicit approval before publication.
- The settings and a verification screenshot or link are recorded in the
  release checklist.

### OPS-02: Enable Security Advisories

**Priority:** P0  
**Owner:** Repository owner / Security owner  
**Depends on:** None

Enable GitHub Security Advisories and verify that the private reporting path in
`SECURITY.md` reaches the maintained repository.

**Acceptance criteria**

- A private security report can be created.
- `SECURITY.md` links to the working private channel.
- A test report is closed without exposing synthetic or real payment data.
- The response owner and backup owner are documented.

### OPS-03: Monitor the v0.1.2 Stabilization Window

**Priority:** P0  
**Owner:** Support owner  
**Depends on:** OPS-01, OPS-02

Monitor issues, discussions, package installation feedback, rollback usage, and
scheduled benchmark runs for one release cycle.

**Acceptance criteria**

- Weekly triage notes record new issues, severity, owner, and disposition.
- Any default-streaming regression has a reproduction or a documented reason
  it cannot be reproduced.
- The rollback switch is tested once in the stabilization window.
- No `0.1.3` is released without a confirmed user-facing defect or security
  fix.

## Epic B: Security And Supply Chain

### SEC-01: Require Signed Release Tags

**Priority:** P0  
**Owner:** Release owner / Security owner  
**Depends on:** OPS-01

Policy: [Release Signing Policy](release-signing.md)

Define the signing authority and verify signed tags in release automation before
building or publishing artifacts.

**Acceptance criteria**

- The signing key owner, rotation, revocation, and recovery process are
  documented.
- Unsigned tags fail before package publication.
- A signed release-candidate rehearsal succeeds.
- A deliberately unsigned rehearsal is shown to be rejected.

### SEC-02: Enforce Full No-Network Testing

**Priority:** P1  
**Owner:** Security owner / QA owner  
**Depends on:** None

Extend the existing pytest socket-denial fixture and document its boundary.
Cover DNS, HTTP clients, raw sockets, subprocess network tools, and async paths
where supported by the test environment.

**Acceptance criteria**

- The full suite runs with external network access denied.
- A deliberate outbound connection attempt fails the test.
- Loopback behavior required by the test runner remains documented.
- The CI job retains the failure output as an artifact when the gate fails.

### SEC-03: Complete Sensitive-Output Coverage

**Priority:** P1  
**Owner:** Security owner / QA owner  
**Depends on:** None

Build a synthetic corpus covering account numbers, IDs, addenda, NOC data,
trace values, malformed records, repair output, diff output, and summaries.

**Acceptance criteria**

- Every MCP tool is exercised with reveal disabled.
- Serialized output, stdout, and stderr contain no original sensitive values.
- Explicit reveal behavior is tested separately and requires configuration.
- The corpus contains no real financial data.

### SEC-04: Automate MCP Registry Publication

**Priority:** P1  
**Owner:** Release owner  
**Depends on:** OPS-01

Add schema validation and controlled Registry publication evidence to the
release process. Keep authentication and approval outside source control.

**Acceptance criteria**

- `server.json` validation runs before publication.
- Package, manifest, tag, and PyPI versions must match.
- A release artifact records Registry validation and publication status.
- Expired authentication fails clearly without publishing partial metadata.

## Epic C: Support And Management

### SUP-01: Run an Incident-Response Rehearsal

**Priority:** P0  
**Owner:** Incident owner  
**Depends on:** OPS-02

Exercise `docs/incident-response.md` using a simulated sensitive-output report.

**Acceptance criteria**

- Intake, severity, containment, evidence handling, communication, recovery,
  and closure steps are completed.
- No sensitive data is copied into public issues or logs.
- A short retrospective records one improvement or confirms no changes needed.

### SUP-02: Establish Maintainer Ownership

**Priority:** P1  
**Owner:** Repository owner  
**Depends on:** OPS-01

Confirm primary and backup owners for security, incidents, releases,
dependencies, Registry publication, and user support.

**Acceptance criteria**

- The ownership table names a primary and backup for each responsibility.
- CODEOWNERS paths match actual ownership.
- Owner changes have a documented handoff process.

### SUP-03: Define Support And Lifecycle Policy

**Priority:** P1  
**Owner:** Support owner / Product owner  
**Depends on:** OPS-03

Publish supported Python and package versions, response expectations,
deprecation rules, security-fix policy, and issue-triage cadence.

**Acceptance criteria**

- Users can identify whether their installed version is supported.
- Public support and private security reporting are clearly separated.
- Deprecation notices include a replacement and timeline.
- Stale issue handling has an explicit cadence and owner.

**Delivery status:** Documentation is published and the conservative
best-effort `v0.1.x` policy is approved. No formal SLA or individual backup
owner is asserted.

## Epic D: Quality And Compatibility

### QA-01: Add Differential Validation Workflow

**Priority:** P1  
**Owner:** QA owner  
**Depends on:** SEC-02

Run the synthetic differential corpus against the approved external reference
implementation when the optional environment is available.

**Acceptance criteria**

- The workflow is optional or scheduled and never requires runtime network access.
- At least 100 deterministic cases run locally.
- Disagreements produce an artifact with rule, input mutation, and triage state.
- Release approval is blocked on unexplained disagreements.

### QA-02: Add Windows To Regular CI

**Priority:** P1  
**Owner:** QA owner  
**Depends on:** None

Add Windows coverage for path resolution, symlinks where supported, encoding,
CLI behavior, package installation, and security fixtures.

**Acceptance criteria**

- Windows runs the normal quality suite on supported Python versions.
- Windows-specific failures are triaged rather than hidden with skips.
- The release matrix includes the supported operating-system policy.

### QA-03: Maintain Streaming Performance Evidence

**Priority:** P1  
**Owner:** Performance owner / QA owner  
**Depends on:** None

Maintain the scheduled cross-platform benchmark and review its artifacts.

**Acceptance criteria**

- Windows, Ubuntu, and macOS run the 100,000-entry benchmark.
- Wall-clock and separate memory measurements are recorded.
- Validity, error count, and platform/Python versions are recorded.
- A regression beyond the approved threshold creates a triage item.
- The rollback switch remains tested for one release cycle.

### QA-04: Review Unverified Reference Data

**Priority:** P1  
**Owner:** Reference-data owner / Product owner  
**Depends on:** None

Review every `UNVERIFIED` rule or reference row before presenting it as
authoritative guidance.

**Acceptance criteria**

- Each row has source URL, retrieval date, reviewer, status, and decision.
- Unverified rows remain visibly labeled in output and documentation.
- Product-owner approval is recorded before any authoritative claim ships.

## Epic E: Product Follow-Up

### PROD-01: Review Custom-Runner Compatibility

**Priority:** P2  
**Owner:** Core owner  
**Depends on:** QA-01, QA-03

Decide whether custom rule runners should receive a supported streaming adapter
or continue using the legacy context path.

**Acceptance criteria**

- The compatibility boundary is documented.
- No custom runner silently changes execution path.
- A benchmark and parity decision is recorded.

### PROD-02: Plan the Next Performance Slice

**Priority:** P2  
**Owner:** Core owner / Performance owner  
**Depends on:** QA-03

Use benchmark profiles to choose the next optimization only after observed
regression evidence. Avoid broad refactors without a parity corpus.

**Acceptance criteria**

- A profile identifies the hotspot.
- The change has a falsifiable before/after benchmark.
- Complete report parity is checked.
- The change is retained only if it improves or clearly stabilizes the target.

## Suggested Execution Order

1. OPS-01 and OPS-02: repository and security controls.
2. SEC-01 and SUP-02: accountable release ownership.
3. SUP-01 and SUP-03: operational readiness.
4. SEC-02 and SEC-03: security regression coverage.
5. QA-01 and QA-02: compatibility and differential quality.
6. QA-03: recurring benchmark review.
7. SEC-04: Registry automation and release evidence.
8. PROD-01 and PROD-02: later product decisions.

## Sprint Reporting Template

Each story update should include:

```text
Story: OPS-01
Status: In Progress | Blocked | Done
Owner: @handle
Evidence: link to PR, workflow, or report
Tests: command and result
Risks: none or explicit risk
Next: one concrete action
```
