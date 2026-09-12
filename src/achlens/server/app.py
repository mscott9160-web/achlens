"""Official MCP SDK v2 server entry point."""

from mcp.server import MCPServer

from .config import ServerConfig
from .prompts import debug_ach_file, explain_returns
from .resources import layouts_resource, reference_resource, rules_resource
from .tools import (
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

_config = ServerConfig.from_environment()
mcp = MCPServer("achlens", version="0.1.2", log_level=_config.log_level)


@mcp.tool()
def server_status() -> dict[str, str]:
    """Return the local achlens server status."""
    return {"name": "achlens", "status": "ready", "transport": "stdio"}


mcp.tool()(validate_ach_file)
mcp.tool()(summarize_ach_file)
mcp.tool()(parse_ach_file)
mcp.tool()(explain_control_totals)
mcp.tool()(check_routing_number)
mcp.tool()(lookup_ach_code)
mcp.tool()(generate_test_ach_file)
mcp.tool()(repair_control_records_tool)
mcp.tool()(diff_ach_files_tool)
mcp.resource(
    "ach://layouts",
    name="layouts",
    description="The packaged ACH record layouts.",
    mime_type="application/json",
)(layouts_resource)
mcp.resource(
    "ach://rules",
    name="rules",
    description="The packaged ACH validation rule catalog.",
    mime_type="application/json",
)(rules_resource)
mcp.resource(
    "ach://reference/{kind}",
    name="reference",
    description="A packaged ACH reference-code table.",
    mime_type="application/json",
)(reference_resource)
mcp.prompt(
    name="debug_ach_file",
    description="Guide deterministic ACH validation and control-total debugging.",
)(debug_ach_file)
mcp.prompt(
    name="explain_returns",
    description="Guide a concise returns and NOCs explanation.",
)(explain_returns)


def run() -> None:
    """Run achlens over the SDK's default stdio transport."""
    mcp.run()


__all__ = [
    "mcp",
    "explain_control_totals",
    "lookup_ach_code",
    "check_routing_number",
    "debug_ach_file",
    "parse_ach_file",
    "reference_resource",
    "run",
    "server_status",
    "summarize_ach_file",
    "rules_resource",
    "layouts_resource",
    "validate_ach_file",
]
