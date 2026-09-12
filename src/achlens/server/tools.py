"""Thin MCP tool adapters over the pure achlens core."""

from dataclasses import asdict
from typing import Literal

from achlens.core.calculators import (
    aba_check_digit,
    batch_entry_addenda_count,
    batch_entry_hash,
    batch_totals,
    block_count,
    file_entry_addenda_count,
    file_entry_hash,
    file_totals,
    valid_routing_number,
)
from achlens.core.data.entry_codes import PRENOTE_CODES
from achlens.core.generator import generate_ach_file
from achlens.core.masking import mask as mask_ach
from achlens.core.model import AchFile, Record
from achlens.core.parser import parse
from achlens.core.reference import lookup_code
from achlens.core.repair import repair_control_records
from achlens.core.validator import validate as validate_core

from .config import ServerConfig
from .inputs import InputResolutionError, resolve_input


def _error(code: str, message: str, hint: str) -> dict[str, object]:
    return {"error": {"code": code, "message": message, "hint": hint}}


def _error_from_exception(error: InputResolutionError) -> dict[str, object]:
    detail = error.error
    return _error(detail.code, detail.message, detail.hint)


def _report_dict(report: object) -> dict[str, object]:
    return asdict(report)  # type: ignore[arg-type]


def validate_ach_file(
    content: str | None = None,
    path: str | None = None,
    reveal_sensitive: bool = False,
    min_severity: Literal["error", "warning", "info"] = "info",
    rule_ids: list[str] | None = None,
) -> dict[str, object]:
    """Validate an ACH file and return structured findings and aggregate counts."""
    del reveal_sensitive  # Validation findings never expose sensitive field values.
    try:
        config = ServerConfig.from_environment()
        resolved = resolve_input(content=content, path=path, config=config)
        report = validate_core(
            resolved.content,
            min_severity=min_severity,
            max_findings=config.max_findings,
            rule_ids=set(rule_ids) if rule_ids is not None else None,
        )
        result = _report_dict(report)
        result["masked"] = True
        result["path_mode"] = resolved.path is not None
        return result
    except InputResolutionError as error:
        return _error_from_exception(error)
    except (UnicodeError, ValueError):
        return _error(
            "NOT_ACH",
            "The input could not be validated as an ACH file.",
            "Provide ACH text with recognizable record types.",
        )
    except Exception:
        return _error(
            "INTERNAL",
            "The validation request could not be completed.",
            "Retry the request without exposing file contents.",
        )


def _field(record: object, name: str) -> str:
    fields = getattr(record, "fields", {})
    field = fields.get(name)
    return field.raw.strip() if field is not None else ""


def _mask_text(value: str) -> str:
    if len(value) <= 4:
        return "*" * len(value)
    return "*" * (len(value) - 4) + value[-4:]


def _dollars(cents: int) -> str:
    return f"${cents // 100:,}.{cents % 100:02d}"


def summarize_ach_file(
    content: str | None = None,
    path: str | None = None,
    reveal_sensitive: bool = False,
) -> dict[str, object]:
    """Summarize ACH structure, totals, SEC codes, returns, and NOCs."""
    del reveal_sensitive
    try:
        config = ServerConfig.from_environment()
        resolved = resolve_input(content=content, path=path, config=config)
        ach_file = parse(resolved.content)
        debit, credit = file_totals(ach_file)
        batches: list[dict[str, object]] = []
        sec_codes: set[str] = set()
        effective_dates: list[str] = []
        company_names: list[str] = []
        prenotes = 0
        returns: list[dict[str, object]] = []
        nocs: list[dict[str, object]] = []
        for batch in ach_file.batches:
            sec = _field(batch.header, "standard_entry_class_code")
            if sec:
                sec_codes.add(sec)
            effective = _field(batch.header, "effective_entry_date")
            if effective:
                effective_dates.append(effective)
            company = _field(batch.header, "company_name")
            if company:
                company_names.append(company)
            batch_debit, batch_credit = 0, 0
            from achlens.core.calculators import batch_totals

            batch_debit, batch_credit = batch_totals(batch)
            batches.append(
                {
                    "batch_number": _field(batch.header, "batch_number"),
                    "service_class_code": _field(batch.header, "service_class_code"),
                    "sec_code": sec,
                    "entry_count": len(batch.entries),
                    "addenda_count": sum(len(entry.addenda) for entry in batch.entries),
                    "debit_total_cents": batch_debit,
                    "credit_total_cents": batch_credit,
                }
            )
            for entry in batch.entries:
                code = _field(entry.detail, "transaction_code")
                if code.isdigit() and int(code) in PRENOTE_CODES:
                    prenotes += 1
                trace = _field(entry.detail, "trace_number")
                for addenda in entry.addenda:
                    addenda_type = _field(addenda, "addenda_type_code")
                    if addenda_type == "99":
                        returns.append(
                            {
                                "trace_number": trace,
                                "return_code": _field(addenda, "return_reason_code"),
                                "title": "Unverified return code",
                                "original_trace": _field(
                                    addenda, "original_entry_trace_number"
                                ),
                            }
                        )
                    elif addenda_type == "98":
                        corrected = _field(addenda, "corrected_data")
                        nocs.append(
                            {
                                "trace_number": trace,
                                "change_code": _field(addenda, "change_code"),
                                "title": "Unverified NOC code",
                                "corrected_data_masked": _mask_text(corrected),
                            }
                        )
        return {
            "summary": {
                "line_count": ach_file.line_count,
                "batch_count": len(ach_file.batches),
                "entry_count": sum(len(batch.entries) for batch in ach_file.batches),
                "addenda_count": sum(
                    len(entry.addenda)
                    for batch in ach_file.batches
                    for entry in batch.entries
                ),
                "total_debit_cents": debit,
                "total_credit_cents": credit,
                "total_debits": _dollars(debit),
                "total_credits": _dollars(credit),
                "sec_codes": sorted(sec_codes),
                "effective_dates": effective_dates,
                "company_names": company_names,
                "prenote_count": prenotes,
                "return_count": len(returns),
                "noc_count": len(nocs),
            },
            "batches": batches,
            "returns": returns,
            "nocs": nocs,
            "masked": True,
            "path_mode": resolved.path is not None,
        }
    except InputResolutionError as error:
        return _error_from_exception(error)
    except (UnicodeError, ValueError):
        return _error(
            "NOT_ACH",
            "The input could not be summarized as an ACH file.",
            "Provide ACH text with recognizable record types.",
        )
    except Exception:
        return _error(
            "INTERNAL",
            "The summary request could not be completed.",
            "Retry the request without exposing file contents.",
        )


def _records(ach_file: AchFile) -> list[Record]:
    records: list[Record] = []
    if ach_file.header is not None:
        records.append(ach_file.header)
    for batch in ach_file.batches:
        if batch.header is not None:
            records.append(batch.header)
        for entry in batch.entries:
            records.append(entry.detail)
            records.extend(entry.addenda)
        if batch.control is not None:
            records.append(batch.control)
    if ach_file.control is not None:
        records.append(ach_file.control)
    records.extend(ach_file.padding)
    records.extend(ach_file.unparsed)
    return records


def parse_ach_file(
    content: str | None = None,
    path: str | None = None,
    reveal_sensitive: bool = False,
    offset: int = 0,
    limit: int = 50,
    record_types: list[str] | None = None,
) -> dict[str, object]:
    """Parse named ACH fields in a bounded page of records."""
    try:
        if offset < 0 or limit < 1 or limit > 500:
            return _error(
                "UNSUPPORTED",
                "Invalid paging values.",
                "Use offset >= 0 and limit from 1 through 500.",
            )
        config = ServerConfig.from_environment()
        resolved = resolve_input(content=content, path=path, config=config)
        parsed = parse(resolved.content)
        selected = _records(parsed)
        if record_types is not None:
            allowed = set(record_types)
            selected = [record for record in selected if record.record_type in allowed]
        reveal = reveal_sensitive and config.allow_reveal
        output = mask_ach(parsed, reveal=reveal)
        masked_by_line = {record.line_number: record for record in _records(output)}
        page = [masked_by_line[record.line_number] for record in selected][
            offset : offset + limit
        ]
        next_offset = offset + limit if offset + limit < len(selected) else None
        return {
            "records": [asdict(record) for record in page],
            "total_records": len(selected),
            "next_offset": next_offset,
            "masked": not reveal,
            "path_mode": resolved.path is not None,
        }
    except InputResolutionError as error:
        return _error_from_exception(error)
    except (UnicodeError, ValueError):
        return _error(
            "NOT_ACH",
            "The input could not be parsed as an ACH file.",
            "Provide ACH text with recognizable record types.",
        )
    except Exception:
        return _error(
            "INTERNAL",
            "The parse request could not be completed.",
            "Retry the request without exposing file contents.",
        )


def _comparison(
    field: str,
    stated: str,
    computed: object,
    explanation: str,
) -> dict[str, object]:
    computed_text = str(computed)
    stated_value = int(stated) if stated.isdigit() else stated
    return {
        "field": field,
        "stated": stated_value,
        "computed": computed,
        "matches": stated_value == computed or stated_value == computed_text,
        "explanation": explanation,
    }


def explain_control_totals(
    content: str | None = None,
    path: str | None = None,
    batch_number: int | None = None,
) -> dict[str, object]:
    """Explain stated versus recomputed batch and file control totals."""
    try:
        config = ServerConfig.from_environment()
        resolved = resolve_input(content=content, path=path, config=config)
        ach_file = parse(resolved.content)
        batches: list[dict[str, object]] = []
        for batch in ach_file.batches:
            number_text = _field(batch.header, "batch_number")
            number = int(number_text) if number_text.isdigit() else None
            if batch_number is not None and number != batch_number:
                continue
            debit, credit = batch_totals(batch)
            expected_hash = batch_entry_hash(batch)
            addends = [
                _field(entry.detail, "receiving_dfi_identification")
                for entry in batch.entries
            ]
            batches.append(
                {
                    "batch_number": number,
                    "comparisons": [
                        _comparison(
                            "entry_addenda_count",
                            _field(batch.control, "entry_addenda_count"),
                            batch_entry_addenda_count(batch),
                            "Count of entry and addenda records in this batch.",
                        ),
                        _comparison(
                            "entry_hash",
                            _field(batch.control, "entry_hash"),
                            expected_hash,
                            "Sum of receiving DFI identifiers: "
                            f"{' + '.join(addends[:20])}"
                            f"{' ...' if len(addends) > 20 else ''}.",
                        ),
                        _comparison(
                            "total_debit_entry_dollar_amount",
                            _field(batch.control, "total_debit_entry_dollar_amount"),
                            debit,
                            "Sum of debit entry amounts in cents.",
                        ),
                        _comparison(
                            "total_credit_entry_dollar_amount",
                            _field(batch.control, "total_credit_entry_dollar_amount"),
                            credit,
                            "Sum of credit entry amounts in cents.",
                        ),
                    ],
                }
            )
        file_debit, file_credit = file_totals(ach_file)
        file_control = ach_file.control
        comparisons = [
            _comparison(
                "batch_count",
                _field(file_control, "batch_count"),
                len(ach_file.batches),
                "Number of parsed batches.",
            ),
            _comparison(
                "block_count",
                _field(file_control, "block_count"),
                block_count(ach_file.line_count),
                "Total physical records divided into ten-record blocks.",
            ),
            _comparison(
                "entry_addenda_count",
                _field(file_control, "entry_addenda_count"),
                file_entry_addenda_count(ach_file),
                "Sum of batch entry/addenda counts.",
            ),
            _comparison(
                "entry_hash",
                _field(file_control, "entry_hash"),
                file_entry_hash(ach_file),
                "Sum of recomputed batch entry hashes, keeping the rightmost "
                "ten digits.",
            ),
            _comparison(
                "total_debit_entry_dollar_amount",
                _field(file_control, "total_debit_entry_dollar_amount"),
                file_debit,
                "Sum of batch debit totals in cents.",
            ),
            _comparison(
                "total_credit_entry_dollar_amount",
                _field(file_control, "total_credit_entry_dollar_amount"),
                file_credit,
                "Sum of batch credit totals in cents.",
            ),
        ]
        return {
            "batches": batches,
            "file": {"comparisons": comparisons},
            "masked": True,
            "path_mode": resolved.path is not None,
        }
    except InputResolutionError as error:
        return _error_from_exception(error)
    except (UnicodeError, ValueError):
        return _error(
            "NOT_ACH",
            "The input could not be analyzed as an ACH file.",
            "Provide ACH text with recognizable records and control fields.",
        )
    except Exception:
        return _error(
            "INTERNAL",
            "The control-total explanation could not be completed.",
            "Retry the request without exposing file contents.",
        )


def check_routing_number(routing_number: str) -> dict[str, object]:
    """Check an ABA routing number's mathematical check digit."""
    if len(routing_number) not in {8, 9} or not routing_number.isdigit():
        return _error(
            "UNSUPPORTED",
            "Routing number must contain exactly 8 or 9 digits.",
            "Provide an eight-digit prefix or a nine-digit routing number.",
        )
    expected = aba_check_digit(routing_number[:8])
    valid = valid_routing_number(routing_number)
    return {
        "input": routing_number,
        "valid": valid,
        "expected_check_digit": str(expected),
        "explanation": (
            "The ABA check digit is mathematically valid; this does not confirm "
            "that the routing number belongs to an active institution."
            if valid
            else "The supplied check digit does not match the ABA calculation; "
            "this check does not query active institutions."
        ),
    }


def lookup_ach_code(kind: str, code: str) -> dict[str, object]:
    """Look up a return, NOC, transaction, SEC, or service-class code."""
    try:
        return lookup_code(kind, code)
    except ValueError:
        return _error(
            "UNSUPPORTED",
            "Reference kind is not supported.",
            "Use return, noc, transaction, sec, or service_class.",
        )


def generate_test_ach_file(
    sec_code: Literal["PPD", "CCD", "CTX", "TEL", "WEB"] = "PPD",
    batches: int = 1,
    entries_per_batch: int = 5,
    service_class: Literal[200, 220, 225] = 200,
    include_prenotes: bool = False,
    include_addenda: bool = False,
    seed: int | None = None,
    effective_date: str | None = None,
    inject_errors: list[str] | None = None,
) -> dict[str, object]:
    """Generate a balanced synthetic ACH file for testing, never transmission."""
    try:
        content = generate_ach_file(
            sec_code=sec_code,
            batches=batches,
            entries_per_batch=entries_per_batch,
            service_class=service_class,
            include_prenotes=include_prenotes,
            include_addenda=include_addenda,
            seed=seed,
            effective_date=effective_date,
            inject_errors=inject_errors,
        )
        parsed = parse(content)
        debit, credit = file_totals(parsed)
        return {
            "content": content,
            "summary": {
                "batch_count": len(parsed.batches),
                "entry_count": sum(len(batch.entries) for batch in parsed.batches),
                "debit_cents": debit,
                "credit_cents": credit,
                "synthetic_only": True,
            },
            "injected": inject_errors or [],
            "seed": seed,
        }
    except ValueError as error:
        return _error(
            "UNSUPPORTED",
            str(error),
            "Use the documented generator limits and supported options.",
        )
    except Exception:
        return _error(
            "INTERNAL",
            "The synthetic file could not be generated.",
            "Retry with smaller limits.",
        )


def repair_control_records_tool(
    content: str | None = None,
    path: str | None = None,
    restore_trailing_spaces: bool = True,
) -> dict[str, object]:
    """Repair derived controls, returning content only in content mode."""
    try:
        config = ServerConfig.from_environment()
        resolved = resolve_input(content=content, path=path, config=config)
        result = repair_control_records(
            resolved.content,
            restore_trailing_spaces=restore_trailing_spaces,
        )
        if result.refused:
            return _error(
                "REPAIR_UNSAFE",
                result.refusal_reason or "Repair was refused as unsafe.",
                "Fix record ordering before attempting control repair.",
            )
        changes = [asdict(change) for change in result.changes]
        if resolved.path is None:
            return {
                "repaired_content": result.repaired_content,
                "changes": changes,
                "valid": result.valid,
                "path_mode": False,
            }
        output = resolved.path.with_name(
            f"{resolved.path.stem}.repaired{resolved.path.suffix}"
        )
        if output.exists():
            return _error(
                "OUTPUT_EXISTS",
                "The repaired output already exists.",
                "Remove or rename the existing output before retrying.",
            )
        output.write_text(result.repaired_content or "", encoding="utf-8")
        return {
            "path": str(output),
            "changes": changes,
            "valid": result.valid,
            "path_mode": True,
        }
    except InputResolutionError as error:
        return _error_from_exception(error)
    except OSError:
        return _error(
            "INTERNAL",
            "The repaired output could not be written.",
            "Check permissions and retry.",
        )
    except Exception:
        return _error(
            "INTERNAL",
            "The repair request could not be completed.",
            "Retry without exposing file contents.",
        )


__all__ = [
    "check_routing_number",
    "explain_control_totals",
    "generate_test_ach_file",
    "repair_control_records_tool",
    "lookup_ach_code",
    "parse_ach_file",
    "summarize_ach_file",
    "validate_ach_file",
]
