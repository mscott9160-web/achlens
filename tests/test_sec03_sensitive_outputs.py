"""SEC-03 synthetic sensitive-output coverage."""

import json

from achlens.core import build_record
from achlens.core.layouts import default_layouts
from achlens.server.tools import (
    check_routing_number,
    diff_ach_files_tool,
    explain_control_totals,
    generate_test_ach_file,
    lookup_ach_code,
    parse_ach_file,
    repair_control_records_tool,
    summarize_ach_file,
    validate_ach_file,
)
from tests.fixtures.builders import set_field, valid_file


def _record(layout: str, **fields: object) -> str:
    return build_record(default_layouts()[layout], **fields)


def _sensitive_corpus() -> tuple[str, tuple[str, ...]]:
    content = valid_file()
    values = (
        "ACCTSECURE1234567",
        "IDSECURE-567890",
        "NOCSECURE-ACCOUNT-123456",
        "123456780000001",
    )
    content = set_field(content, 3, "entry_detail_ppd", "dfi_account_number", values[0])
    content = set_field(
        content,
        3,
        "entry_detail_ppd",
        "individual_identification_number",
        values[1],
    )
    content = set_field(content, 3, "entry_detail_ppd", "trace_number", 123456780000001)
    noc = _record(
        "addenda_98_noc",
        record_type_code=7,
        addenda_type_code=98,
        change_code="C01",
        original_entry_trace_number=123456780000001,
        original_receiving_dfi_identification=12345678,
        corrected_data=values[2],
        trace_number=123456780000002,
    )
    lines = content.splitlines()
    lines[2] = lines[2][:78] + "1" + lines[2][79:]
    return "\n".join(lines[:3] + [noc] + lines[3:]), values


def test_structured_tool_paths_mask_sensitive_values_and_raw_paths_validate(
    capsys,
) -> None:
    content, sensitive_values = _sensitive_corpus()
    malformed = content.replace("\n", "\n\x80", 1)
    repaired_input = generate_test_ach_file(
        entries_per_batch=2,
        seed=8,
        effective_date="260911",
        inject_errors=["BC002"],
    )["content"]

    generated = generate_test_ach_file(seed=9, effective_date="260911")
    repaired = repair_control_records_tool(content=repaired_input)
    structured_outputs = [
        {"server_status": {"name": "achlens", "status": "ready"}},
        validate_ach_file(content=malformed),
        summarize_ach_file(content=content),
        parse_ach_file(content=content),
        explain_control_totals(content=content),
        check_routing_number("123456780"),
        lookup_ach_code("return", "R03"),
        generated["summary"],
        {key: value for key, value in repaired.items() if key != "repaired_content"},
        diff_ach_files_tool(left_content=content, right_content=malformed),
    ]

    captured = capsys.readouterr()
    serialized = (
        json.dumps(structured_outputs, sort_keys=True) + captured.out + captured.err
    )
    for value in sensitive_values:
        assert value not in serialized

    generated_content = generated["content"]
    assert isinstance(generated_content, str)
    assert generated["summary"]["synthetic_only"] is True
    assert validate_ach_file(content=generated_content)["valid"] is True

    repaired_content = repaired["repaired_content"]
    assert isinstance(repaired_content, str)
    assert repaired["valid"] is True
    assert validate_ach_file(content=repaired_content)["valid"] is True


def test_explicit_reveal_requires_configuration(monkeypatch) -> None:
    content, sensitive_values = _sensitive_corpus()
    hidden = parse_ach_file(content=content, reveal_sensitive=True)
    assert hidden["masked"] is True
    assert sensitive_values[0] not in json.dumps(hidden)

    monkeypatch.setenv("ACHLENS_ALLOW_REVEAL", "1")
    revealed = parse_ach_file(content=content, reveal_sensitive=True)
    assert revealed["masked"] is False
    assert sensitive_values[0] in json.dumps(revealed)
