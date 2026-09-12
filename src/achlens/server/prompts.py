"""MCP workflow prompts for deterministic ACH debugging."""


def debug_ach_file() -> str:
    """Guide a model through validation, totals, and optional repair."""
    return (
        "Debug this ACH file using deterministic tools. First call "
        "validate_ach_file. If any BC or FC rule fires, call "
        "explain_control_totals. Explain only findings and computed values "
        "returned by the tools. Offer repair_control_records only after "
        "confirming the user wants derived fields repaired. Do not invent "
        "bank rules, compliance advice, or sensitive values."
    )


def explain_returns() -> str:
    """Guide a model through a returns and NOCs summary."""
    return (
        "Summarize ACH returns and notifications of change for an operations "
        "audience. Call summarize_ach_file first, then explain each returned "
        "code using lookup_ach_code. Preserve UNVERIFIED labels and masked "
        "corrected data. Do not provide legal, compliance, or banking advice."
    )


__all__ = ["debug_ach_file", "explain_returns"]
