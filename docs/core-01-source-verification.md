# CORE-01 Source Verification

Verified against the public Nacha ACH Guide for Developers:

- Source: https://achdevguide.nacha.org/ach-file-details
- Retrieved: 2026-09-11
- Scope: common file, batch, entry, addenda, and SEC descriptions exposed on
  the public guide

## Confirmed

- File records are fixed-width 94-character records.
- File header positions and constants match the guide: priority `01`, blank plus
  nine-digit destination/origin convention, `YYMMDD`, `HHMM`, file ID modifier,
  `094`, blocking factor `10`, and format code `1`.
- File control positions and semantics match the implementation: batch count,
  block count, entry/addenda count, entry hash, debit total, credit total, and
  reserved field.
- Batch header positions match the implementation, including SEC code,
  effective entry date, settlement date, ODFI identification, and ascending
  batch number.
- Batch control positions match the implementation, including entry/addenda
  count, entry hash, debit/credit totals, company identification, ODFI, and
  batch number.
- PPD and CCD entry positions match the implementation.
- PPD/CCD/WEB addenda type `05`, sequence number `0001`, and parent trace
  suffix linkage match the guide.
- The guide identifies common SEC codes ARC, BOC, CCD, CIE, CTX, IAT, POP, POS,
  PPD, RCK, TEL, and WEB. These are now recognized as standard SEC identifiers;
  only PPD, CCD, and WEB have deep v1 entry layouts.

## Corrected Discrepancy

### WEB Payment Type Code

The previous implementation treated only `B`, `R`, and `S` as allowed WEB
payment type values. The official guide states that recurring WEB/TEL entries
use `R`, single-entry TEL uses `S` or may be space-filled, single-entry WEB uses
`S`, and that other two-character originator-significance values are allowed
without a standardized interpretation.

The validator now checks only the structural two-character alphanumeric shape
and does not reject arbitrary originator-significance values. The reference
catalog keeps this area unverified for business interpretation.

## Still Unverified

The public guide is a high-level reference and points to the Nacha Operating
Rules for complete requirements. The following remain `UNVERIFIED` until the
Product Owner approves a first-party source and interpretation:

- Full transaction-code table and reversal/return/NOC edge cases.
- Return reason titles, timeframes, and NOC change-code descriptions.
- Bank-specific Immediate Origin/Destination conventions.
- Originator status code semantics beyond structural handling.
- IAT-specific record layouts and processing rules.
- Health-care EFT and other SEC-specific addenda business content.

No release should present these unresolved items as authoritative compliance or
banking guidance.
