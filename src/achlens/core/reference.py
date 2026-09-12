"""Small, explicitly sourced ACH code catalog for lookup tools."""

from dataclasses import asdict, dataclass
from difflib import get_close_matches


@dataclass(frozen=True)
class ReferenceEntry:
    code: str
    title: str
    description: str
    source: str
    status: str
    details: dict[str, str]


def _entry(
    code: str, title: str, description: str, *, source: str = "achlens convention"
) -> ReferenceEntry:
    return ReferenceEntry(code, title, description, source, "UNVERIFIED", {})


_TRANSACTION = {
    code: _entry(code, title, "Transaction-code category from the achlens v1 table.")
    for code, title in {
        "21": "Automated return/NOC credit, checking",
        "22": "Checking credit",
        "23": "Checking credit prenote",
        "24": "Checking zero-dollar credit",
        "26": "Automated return/NOC debit, checking",
        "27": "Checking debit",
        "28": "Checking debit prenote",
        "29": "Checking zero-dollar debit",
        "31": "Automated return/NOC credit, savings",
        "32": "Savings credit",
        "33": "Savings credit prenote",
        "34": "Savings zero-dollar credit",
        "36": "Automated return/NOC debit, savings",
        "37": "Savings debit",
        "38": "Savings debit prenote",
        "39": "Savings zero-dollar debit",
        "41": "Automated return/NOC credit, general ledger",
        "42": "General-ledger credit",
        "43": "General-ledger credit prenote",
        "44": "General-ledger zero-dollar credit",
        "46": "Automated return/NOC debit, general ledger",
        "47": "General-ledger debit",
        "48": "General-ledger debit prenote",
        "49": "General-ledger zero-dollar debit",
        "51": "Automated return/NOC credit, loan",
        "52": "Loan credit",
        "53": "Loan credit prenote",
        "54": "Loan zero-dollar credit",
        "55": "Loan debit reversal",
        "56": "Automated return/NOC debit, loan",
    }.items()
}
_SEC = {
    code: _entry(code, title, "Standard Entry Class code recognized by achlens.")
    for code, title in {
        "PPD": "Prearranged Payment and Deposit",
        "CCD": "Corporate Credit or Debit",
        "WEB": "Internet-initiated entry",
        "CTX": "Corporate Trade Exchange",
        "IAT": "International ACH Transaction",
        "TEL": "Telephone-initiated entry",
    }.items()
}
_SERVICE_CLASS = {
    code: _entry(code, title, "Service class code recognized by achlens.")
    for code, title in {
        "200": "Mixed debits and credits",
        "220": "Credits only",
        "225": "Debits only",
        "280": "Automated accounting advices",
    }.items()
}
_RETURN = {
    code: _entry(code, title, "Return-code title is an unverified seed value.")
    for code, title in {
        "R01": "Insufficient Funds",
        "R02": "Account Closed",
        "R03": "No Account / Unable to Locate Account",
        "R04": "Invalid Account Number Structure",
        "R05": "Unauthorized Debit to Consumer Account Using Corporate SEC Code",
        "R06": "Returned per ODFI's Request",
        "R07": "Authorization Revoked by Customer",
        "R08": "Payment Stopped",
        "R09": "Uncollected Funds",
        "R10": "Customer Advises Originator Not Known / Not Authorized",
        "R11": "Customer Advises Entry Not in Accordance with Authorization Terms",
        "R12": "Account Sold to Another DFI",
        "R13": "Invalid ACH Routing Number",
        "R14": "Representative Payee Deceased or Unable to Continue",
        "R15": "Beneficiary or Account Holder Deceased",
        "R16": "Account Frozen / Entry Returned per OFAC Instruction",
        "R17": "File Record Edit Criteria",
        "R20": "Non-Transaction Account",
        "R23": "Credit Entry Refused by Receiver",
        "R24": "Duplicate Entry",
        "R29": "Corporate Customer Advises Not Authorized",
    }.items()
}
_NOC = {
    code: _entry(code, title, "NOC-code title is an unverified seed value.")
    for code, title in {
        "C01": "Incorrect Account Number",
        "C02": "Incorrect Routing Number",
        "C03": "Incorrect Routing and Account Number",
        "C04": "Incorrect Individual or Receiving Company Name",
        "C05": "Incorrect Transaction Code",
        "C06": "Incorrect Account Number and Transaction Code",
        "C07": "Incorrect Routing, Account, and Transaction Code",
        "C09": "Incorrect Individual Identification Number",
    }.items()
}

_CATALOG = {
    "transaction": _TRANSACTION,
    "sec": _SEC,
    "service_class": _SERVICE_CLASS,
    "return": _RETURN,
    "noc": _NOC,
}


def reference_catalog(kind: str) -> dict[str, dict[str, object]]:
    """Return all local reference rows for a supported lookup kind."""
    catalog = _CATALOG.get(kind)
    if catalog is None:
        raise ValueError(f"unsupported reference kind: {kind}")
    return {code: asdict(entry) for code, entry in catalog.items()}


def lookup_code(kind: str, code: str) -> dict[str, object]:
    """Return a structured reference entry or close matches."""
    catalog = _CATALOG.get(kind)
    if catalog is None:
        raise ValueError(f"unsupported reference kind: {kind}")
    normalized = code.strip().upper()
    entry = catalog.get(normalized)
    if entry is not None:
        return asdict(entry)
    return {
        "code": normalized,
        "found": False,
        "title": "Code not found",
        "description": "No matching code exists in the local achlens catalog.",
        "source": "achlens convention",
        "status": "UNVERIFIED",
        "close_matches": get_close_matches(normalized, catalog, n=3, cutoff=0.4),
    }


__all__ = ["ReferenceEntry", "lookup_code", "reference_catalog"]
