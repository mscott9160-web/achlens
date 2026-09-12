"""Deterministic synthetic ACH file generation."""

import random
from datetime import date, datetime

from .builder import build_record
from .calculators import aba_check_digit
from .layouts import default_layouts

_ROUTING_PREFIXES = ("12345678", "23138010", "32407119", "04400003")
_NAMES = ("TEST PERSON", "SYNTHETIC USER", "SAMPLE RECEIVER", "ACHLENS DEMO")


def _effective_date(value: str | None) -> int:
    if value is None:
        return int(date.today().strftime("%y%m%d"))
    try:
        datetime.strptime(value, "%y%m%d")
    except ValueError as error:
        raise ValueError("effective_date must be a valid YYMMDD date") from error
    return int(value)


def _routing(rng: random.Random) -> tuple[str, str]:
    prefix = rng.choice(_ROUTING_PREFIXES)
    return prefix, str(aba_check_digit(prefix))


def _layout_for_sec(sec_code: str) -> str:
    return {
        "PPD": "entry_detail_ppd",
        "CCD": "entry_detail_ccd",
        "WEB": "entry_detail_web",
    }[sec_code]


def generate_ach_file(
    *,
    sec_code: str = "PPD",
    batches: int = 1,
    entries_per_batch: int = 5,
    service_class: int = 200,
    include_prenotes: bool = False,
    include_addenda: bool = False,
    seed: int | None = None,
    effective_date: str | None = None,
) -> str:
    """Generate a balanced synthetic ACH file for local testing only."""
    sec_code = sec_code.upper()
    if sec_code not in {"PPD", "CCD", "WEB"}:
        raise ValueError("sec_code must be PPD, CCD, or WEB")
    if not 1 <= batches <= 50:
        raise ValueError("batches must be between 1 and 50")
    if not 1 <= entries_per_batch <= 10_000:
        raise ValueError("entries_per_batch must be between 1 and 10000")
    if service_class not in {200, 220, 225}:
        raise ValueError("service_class must be 200, 220, or 225")
    effective = _effective_date(effective_date)
    rng = random.Random(seed)
    layouts = default_layouts()
    lines: list[str] = [
        build_record(
            layouts["file_header"],
            record_type_code=1,
            priority_code=1,
            immediate_destination=" 123456780",
            immediate_origin=" 987654321",
            file_creation_date=effective,
            file_id_modifier="A",
            record_size=94,
            blocking_factor=10,
            format_code=1,
            immediate_destination_name="SYNTHETIC BANK",
            immediate_origin_name="ACHLENS TEST",
        )
    ]
    batch_totals: list[tuple[int, int, int, int]] = []
    layout_name = _layout_for_sec(sec_code)
    trace_sequence = 0
    for batch_number in range(1, batches + 1):
        odfi = "12345678"
        lines.append(
            build_record(
                layouts["batch_header"],
                record_type_code=5,
                service_class_code=service_class,
                company_name="ACHLENS TEST",
                company_identification="9876543210",
                standard_entry_class_code=sec_code,
                company_entry_description="TESTPAY",
                effective_entry_date=effective,
                originator_status_code=1,
                originating_dfi_identification=odfi,
                batch_number=batch_number,
            )
        )
        entry_hash = 0
        debit_total = 0
        credit_total = 0
        count = 0
        for entry_number in range(1, entries_per_batch + 1):
            trace_sequence += 1
            prefix, check_digit = _routing(rng)
            is_credit = service_class == 220 or (
                service_class == 200 and entry_number % 2 == 1
            )
            if service_class == 225:
                is_credit = False
            if include_prenotes and entry_number == 1:
                transaction_code = 23 if is_credit else 28
                amount = 0
            else:
                transaction_code = 22 if is_credit else 27
                amount = rng.randint(100, 10_000)
            trace = f"{odfi}{trace_sequence:07d}"
            fields: dict[str, object] = {
                "record_type_code": 6,
                "transaction_code": transaction_code,
                "receiving_dfi_identification": prefix,
                "check_digit": check_digit,
                "dfi_account_number": f"TEST{batch_number:02d}{entry_number:05d}",
                "amount": amount,
                "individual_name": _NAMES[(entry_number - 1) % len(_NAMES)],
                "addenda_record_indicator": int(include_addenda),
                "trace_number": trace,
            }
            if sec_code == "CCD":
                fields["receiving_company_name"] = fields.pop("individual_name")
            if sec_code == "WEB":
                fields["payment_type_code"] = "S"
            lines.append(build_record(layouts[layout_name], **fields))
            entry_hash += int(prefix)
            count += 1
            if is_credit:
                credit_total += amount
            else:
                debit_total += amount
            if include_addenda:
                lines.append(
                    build_record(
                        layouts["addenda_05"],
                        record_type_code=7,
                        addenda_type_code=5,
                        payment_related_information="ACHLENS SYNTHETIC ADDENDA",
                        addenda_sequence_number=1,
                        entry_detail_sequence_number=trace[-7:],
                    )
                )
                count += 1
        lines.append(
            build_record(
                layouts["batch_control"],
                record_type_code=8,
                service_class_code=service_class,
                entry_addenda_count=count,
                entry_hash=entry_hash,
                total_debit_entry_dollar_amount=debit_total,
                total_credit_entry_dollar_amount=credit_total,
                company_identification="9876543210",
                originating_dfi_identification=odfi,
                batch_number=batch_number,
            )
        )
        batch_totals.append((count, entry_hash, debit_total, credit_total))
    total_entries = sum(item[0] for item in batch_totals)
    total_hash = sum(item[1] for item in batch_totals) % 10_000_000_000
    total_debit = sum(item[2] for item in batch_totals)
    total_credit = sum(item[3] for item in batch_totals)
    lines.append(
        build_record(
            layouts["file_control"],
            record_type_code=9,
            batch_count=batches,
            block_count=(len(lines) + 1 + 9) // 10,
            entry_addenda_count=total_entries,
            entry_hash=total_hash,
            total_debit_entry_dollar_amount=total_debit,
            total_credit_entry_dollar_amount=total_credit,
        )
    )
    lines.extend(["9" * 94] * ((-len(lines)) % 10))
    return "\n".join(lines)


__all__ = ["generate_ach_file"]
