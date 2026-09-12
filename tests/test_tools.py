"""MCP-03/MCP-04 tool adapter tests."""

from achlens.core import build_record
from achlens.core.layouts import default_layouts
from achlens.server.tools import (
    check_routing_number,
    explain_control_totals,
    generate_test_ach_file,
    lookup_ach_code,
    parse_ach_file,
    summarize_ach_file,
    validate_ach_file,
)
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


def test_parse_tool_pages_and_filters_records() -> None:
    content = valid_file()
    first_page = parse_ach_file(content=content, offset=0, limit=2)
    assert first_page["total_records"] == 10
    assert len(first_page["records"]) == 2
    assert first_page["next_offset"] == 2
    entries = parse_ach_file(content=content, record_types=["6"])
    assert entries["total_records"] == 1
    assert entries["records"][0]["record_type"] == "6"


def test_parse_tool_rejects_invalid_page_size() -> None:
    result = parse_ach_file(content=valid_file(), limit=501)
    assert result["error"]["code"] == "UNSUPPORTED"


def test_explain_control_totals_reports_recomputed_values() -> None:
    result = explain_control_totals(content=valid_file())
    assert result["batches"][0]["comparisons"][1]["field"] == "entry_hash"
    assert all(item["matches"] for item in result["batches"][0]["comparisons"])
    assert all(item["matches"] for item in result["file"]["comparisons"])


def test_explain_control_totals_can_select_a_batch() -> None:
    result = explain_control_totals(content=valid_file(), batch_number=2)
    assert result["batches"] == []


def test_check_routing_number_reports_check_digit_and_limitation() -> None:
    valid = check_routing_number("123456780")
    assert valid["valid"] is True
    assert valid["expected_check_digit"] == "0"
    assert "active institution" in valid["explanation"]

    invalid = check_routing_number("123456781")
    assert invalid["valid"] is False
    assert invalid["expected_check_digit"] == "0"


def test_check_routing_prefix_and_bad_input() -> None:
    prefix = check_routing_number("12345678")
    assert prefix["valid"] is True
    assert prefix["expected_check_digit"] == "0"
    error = check_routing_number("not-a-routing-number")
    assert error["error"]["code"] == "UNSUPPORTED"


def test_lookup_ach_code_returns_unverified_reference_rows() -> None:
    result = lookup_ach_code("return", "R03")
    assert result["code"] == "R03"
    assert result["status"] == "UNVERIFIED"
    assert result["title"] == "No Account / Unable to Locate Account"

    transaction = lookup_ach_code("transaction", "22")
    assert transaction["title"] == "Checking credit"


def test_lookup_ach_code_returns_close_matches_and_structured_errors() -> None:
    unknown = lookup_ach_code("noc", "C0")
    assert unknown["found"] is False
    assert unknown["close_matches"]
    error = lookup_ach_code("unsupported", "R03")
    assert error["error"]["code"] == "UNSUPPORTED"


def test_generate_test_file_returns_seeded_synthetic_content() -> None:
    result = generate_test_ach_file(
        sec_code="WEB",
        batches=2,
        entries_per_batch=2,
        service_class=220,
        include_prenotes=True,
        seed=7,
        effective_date="260911",
    )
    assert result["summary"]["synthetic_only"] is True
    assert result["summary"]["batch_count"] == 2
    assert len(result["content"].splitlines()) % 10 == 0


def test_generate_test_file_returns_structured_limit_error() -> None:
    result = generate_test_ach_file(entries_per_batch=10_001)
    assert result["error"]["code"] == "UNSUPPORTED"


def test_generate_test_file_propagates_error_injections() -> None:
    result = generate_test_ach_file(
        entries_per_batch=2,
        seed=7,
        effective_date="260911",
        inject_errors=["BC002"],
    )
    assert result["injected"] == ["BC002"]
