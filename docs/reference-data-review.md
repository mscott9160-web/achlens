# Reference Data Review Register

**Status:** Review register complete; product-owner approval pending for
unverified interpretations.  
**Scope:** ACH layouts, rule descriptions, transaction codes, returns, NOCs,
SEC-specific content, and Federal Reserve calendar data.  
**Policy:** `UNVERIFIED` content must not be presented as authoritative banking
or compliance guidance.

## Review Method

Each row records the source currently used by the project, its verification
state, the reviewer and decision fields, and the action required before an
authoritative claim can ship. Public ACH guide claims are limited to the scope
listed in [CORE-01 source verification](core-01-source-verification.md).

| Area | Current source | Retrieved | Status | Reviewer | Decision | Release treatment |
| --- | --- | --- | --- | --- | --- | --- |
| Common file, batch, entry, and addenda positions | [Nacha ACH Guide for Developers](https://achdevguide.nacha.org/ach-file-details) | 2026-09-11 | VERIFIED for documented scope | Repository owner | Confirmed structural implementation | May describe structural behavior; not full Operating Rules compliance |
| Federal Reserve holiday dates | [Federal Reserve K.8](https://www.federalreserve.gov/aboutthefed/k8.htm) | 2026-09-12 | VERIFIED | Repository owner | Confirmed calendar source and retrieval metadata | May support calendar warnings |
| Transaction-code meanings and reversal edge cases | No approved first-party source recorded | n/a | UNVERIFIED | Pending product owner | Pending source and interpretation approval | Keep visibly unverified; no authoritative titles or compliance claims |
| Return reason titles and timeframes | No approved first-party source recorded | n/a | UNVERIFIED | Pending product owner | Pending source and interpretation approval | Keep visibly unverified; structural validation only |
| NOC change-code descriptions and corrected-data semantics | No approved first-party source recorded | n/a | UNVERIFIED | Pending product owner | Pending source and interpretation approval | Keep visibly unverified; structural validation only |
| Immediate Origin/Destination bank conventions | Bank-specific and not approved | n/a | UNVERIFIED | Pending product owner | Pending scope decision | Do not claim a universal bank convention |
| Originator status code business meaning | No approved first-party source recorded | n/a | UNVERIFIED | Pending product owner | Pending source and interpretation approval | Structural handling only |
| IAT layouts and processing rules | No approved first-party source recorded | n/a | UNVERIFIED | Pending product owner | Pending source and interpretation approval | IAT deep validation remains out of scope |
| Health-care EFT and other SEC-specific addenda content | No approved first-party source recorded | n/a | UNVERIFIED | Pending product owner | Pending source and interpretation approval | Do not present business content as authoritative |

## Existing Data Invariants

The repository currently enforces these safety rules:

- `rules.yaml` marks unapproved catalog descriptions `UNVERIFIED`.
- MCP lookup and explanation outputs preserve source/status metadata.
- Documentation identifies the public guide as high-level and excludes complete
  Nacha Operating Rules claims.
- Synthetic fixtures and examples are required; no real payment data belongs in
  this register or its evidence.

## Approval Gate

QA-04 is complete only when the Product owner records, for each `UNVERIFIED`
row either:

1. an approved first-party source URL, retrieval date, reviewer, and approved
   interpretation; or
2. an explicit decision to keep the row unverified and out of authoritative
   output.

Until then, release approval must preserve the `UNVERIFIED` labels and the
release checklist must record this unresolved reference-data risk.

## Evidence Template

```text
Area:
Source URL:
Retrieved:
Reviewer:
Status: VERIFIED | UNVERIFIED | REJECTED
Decision:
Release treatment:
Approval account/date:
```
