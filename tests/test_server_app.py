"""MCP-02 server registration checks."""

import asyncio

import pytest

mcp = pytest.importorskip("mcp")
from achlens.server.app import mcp as server  # noqa: E402


def test_server_registers_expected_tool_without_protocol_output() -> None:
    tools = asyncio.run(server.list_tools())
    assert [tool.name for tool in tools] == [
        "server_status",
        "validate_ach_file",
        "summarize_ach_file",
        "parse_ach_file",
        "explain_control_totals",
        "check_routing_number",
        "lookup_ach_code",
    ]
    assert tools[0].description == "Return the local achlens server status."


def test_server_status_tool_returns_structured_result() -> None:
    result = asyncio.run(server.call_tool("server_status", {}))
    assert result.structured_content == {
        "name": "achlens",
        "status": "ready",
        "transport": "stdio",
    }


def test_validate_tool_returns_structured_report_and_errors() -> None:
    valid_result = asyncio.run(server.call_tool("validate_ach_file", {"content": ""}))
    assert valid_result.structured_content["valid"] is False
    assert valid_result.structured_content["masked"] is True

    missing_result = asyncio.run(server.call_tool("validate_ach_file", {}))
    assert missing_result.structured_content["error"]["code"] == "INPUT_MISSING"
