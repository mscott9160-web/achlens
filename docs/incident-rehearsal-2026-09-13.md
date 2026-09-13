# Incident Response Rehearsal

**Date:** 2026-09-13  
**Status:** Closed rehearsal  
**Data classification:** Synthetic-only exercise

## Scenario

A synthetic user reports that a structured MCP response contains the original
NOC trace value `123456780000001` when reveal is disabled. The report names a
published version and includes a minimal generated fixture. No real ACH file,
account number, credential, or user data is used.

This scenario models the SEC-03 masking defect fixed on
`development/test-com`; it is a rehearsal record, not a claim that the
published `v0.1.2` package currently has this defect.

## Intake And Severity

- **Intake:** Private GitHub Security Advisory.
- **Coordinator:** Repository owner until another maintainer explicitly
  consents.
- **Severity:** High during triage because sensitive structured output could be
  exposed to a local caller; impact is limited to the affected output path.
- **Initial scope:** Structured MCP/tool serialization only. Runtime network
  access and raw synthetic fixed-width generator content are out of scope for
  this scenario.
- **Immediate decision:** Pause the next release and do not publish a new
  artifact until the regression is reproduced or ruled out.

## Containment

1. Keep the report private and remove any sensitive values from copied logs.
2. Reproduce with a synthetic fixture containing only the placeholder values
   above.
3. Set `ACHLENS_DISABLE_STREAMING_VALIDATION=1` if validation-path behavior
   must be isolated while investigating; this is an internal rollback switch,
   not a masking control.
4. Disable or patch the affected structured output path before release.
5. Preserve the vulnerable version/commit and sanitized reproduction metadata.

No credential rotation is required because the scenario contains no credential
exposure and the runtime does not transmit data.

## Evidence And Investigation

Retain only:

- Affected version or commit.
- Sanitized synthetic fixture identifier.
- Tool name and output field.
- Reproduction command and expected masked behavior.
- Test result and review link.

Do not retain the original sensitive value in public issues, release notes,
logs, artifacts, or screenshots. The placeholder in this document is synthetic
and must not be replaced with production data.

## Remediation And Validation

The simulated fix adds the sensitive field to the shared masking policy and
adds a regression assertion across structured tool output, stdout, and stderr.
Raw fixed-width generator and repair responses remain structurally valid and
synthetic; they are not routed through structured summaries.

Validation evidence for the rehearsal:

- SEC-03 focused regression tests pass.
- Full test suite passes.
- Ruff and strict mypy pass.
- `pip-audit` reports no known vulnerabilities.
- `uv lock --check` passes.
- `git diff --check` passes.
- The synthetic raw generator and repair content still validate as ACH text.

## Communication And Closure

- The private reporter receives acknowledgement and a sanitized status update.
- Affected releases remain blocked until validation passes.
- A public advisory or release note is published only after impact and fix
  scope are confirmed.
- Closure requires the coordinator to record mitigation, validation evidence,
  disclosure decision, and follow-up owner.

**Rehearsal outcome:** The runbook handled intake, severity, containment,
evidence handling, remediation, validation, communication, and closure without
exposing sensitive data. No production release was withdrawn because this was a
simulation.

## Follow-Up

- Keep SEC-03 corpus-wide privacy tests in the release gate.
- Repeat this rehearsal after a second maintainer accepts incident backup
  ownership.
- Link any real advisory or corrective release from the private incident record,
  not from this synthetic exercise.
