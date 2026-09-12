"""Thin MCP tool adapters over the pure achlens core."""

from dataclasses import asdict
from typing import Literal

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
        return _error("NOT_ACH", "The input could not be validated as an ACH file.", "Provide ACH text with recognizable record types.")
    except Exception:
        return _error("INTERNAL", "The validation request could not be completed.", "Retry the request without exposing file contents.")


__all__ = ["validate_ach_file"]