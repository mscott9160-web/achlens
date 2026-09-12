"""Thin MCP tool adapters over the pure achlens core."""

from dataclasses import asdict
from typing import Literal

from achlens.core.validator import validate as validate_core
from achlens.core.calculators import file_totals
from achlens.core.parser import parse
from achlens.core.data.entry_codes import PRENOTE_CODES

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
        return _error("NOT_ACH", "The input could not be validated as an ACH file.", "Provide ACH text with recognizable record types.")
    except Exception:
        return _error("INTERNAL", "The validation request could not be completed.", "Retry the request without exposing file contents.")


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
            batches.append({
                "batch_number": _field(batch.header, "batch_number"),
                "service_class_code": _field(batch.header, "service_class_code"),
                "sec_code": sec,
                "entry_count": len(batch.entries),
                "addenda_count": sum(len(entry.addenda) for entry in batch.entries),
                "debit_total_cents": batch_debit,
                "credit_total_cents": batch_credit,
            })
            for entry in batch.entries:
                code = _field(entry.detail, "transaction_code")
                if code.isdigit() and int(code) in PRENOTE_CODES:
                    prenotes += 1
                trace = _field(entry.detail, "trace_number")
                for addenda in entry.addenda:
                    addenda_type = _field(addenda, "addenda_type_code")
                    if addenda_type == "99":
                        returns.append({
                            "trace_number": trace,
                            "return_code": _field(addenda, "return_reason_code"),
                            "title": "Unverified return code",
                            "original_trace": _field(addenda, "original_entry_trace_number"),
                        })
                    elif addenda_type == "98":
                        corrected = _field(addenda, "corrected_data")
                        nocs.append({
                            "trace_number": trace,
                            "change_code": _field(addenda, "change_code"),
                            "title": "Unverified NOC code",
                            "corrected_data_masked": _mask_text(corrected),
                        })
        return {
            "summary": {
                "line_count": ach_file.line_count,
                "batch_count": len(ach_file.batches),
                "entry_count": sum(len(batch.entries) for batch in ach_file.batches),
                "addenda_count": sum(len(entry.addenda) for batch in ach_file.batches for entry in batch.entries),
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
        return _error("NOT_ACH", "The input could not be summarized as an ACH file.", "Provide ACH text with recognizable record types.")
    except Exception:
        return _error("INTERNAL", "The summary request could not be completed.", "Retry the request without exposing file contents.")


__all__ = ["summarize_ach_file", "validate_ach_file"]