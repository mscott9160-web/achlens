"""MCP-03/MCP-04 tool adapter tests."""

from achlens.core import build_record
from achlens.core.layouts import default_layouts
from achlens.server.tools import summarize_ach_file, validate_ach_file
from tests.fixtures.builders import valid_file


def _record(layout: str, **fields: object) -> str:
    return build_record(default_layouts()[layout], **fields)


def test_validate_tool_returns_structured_error_for_missing_input() -> None:
    result = validate_ach_file()
    assert result["error"]["code"] == "INPUT_MISSING"


def test_summary_reports_totals_and_batches() -> None:
    result = summarize_ach_file(content=valid_file())
    assert result["masked"] is True
    summary = result["summary"]
    assert summary["batch_count"] == 1
    assert summary["entry_count"] == 1
    assert summary["total_credit_cents"] == 100
    assert summary["total_credits"] == "$1.00"
    assert result["batches"][0]["sec_code"] == "PPD"


def test_summary_masks_noc_corrected_data() -> None:
    lines = valid_file().splitlines()
    lines[2] = lines[2][:78] + "1" + lines[2][79:]
    noc = _record(
        "addenda_98_noc",
        record_type_code=7,
        addenda_type_code=98,
        change_code="C01",
        original_entry_trace_number=123456780000001,
        original_receiving_dfi_identification=12345678,
        corrected_data="ACCOUNT-123456789",
        trace_number=123456780000002,
    )
    result = summarize_ach_file(content="\n".join(lines[:3] + [noc] + lines[3:]))
    assert result["nocs"][0]["change_code"] == "C01"
    assert result["nocs"][0]["corrected_data_masked"].endswith("6789")
    assert "ACCOUNT-123456789" not in str(result)
