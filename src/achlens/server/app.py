"""Official MCP SDK v2 server entry point."""

from mcp.server import MCPServer

from .config import ServerConfig
from .tools import (
    check_routing_number,
    explain_control_totals,
    parse_ach_file,
    summarize_ach_file,
    validate_ach_file,
)

_config = ServerConfig.from_environment()
mcp = MCPServer("achlens", version="0.1.0", log_level=_config.log_level)


@mcp.tool()
def server_status() -> dict[str, str]:
    """Return the local achlens server status."""
    return {"name": "achlens", "status": "ready", "transport": "stdio"}


mcp.tool()(validate_ach_file)
mcp.tool()(summarize_ach_file)
mcp.tool()(parse_ach_file)
mcp.tool()(explain_control_totals)
mcp.tool()(check_routing_number)


def run() -> None:
    """Run achlens over the SDK's default stdio transport."""
    mcp.run()


__all__ = [
    "mcp",
    "explain_control_totals",
    "check_routing_number",
    "parse_ach_file",
    "run",
    "server_status",
    "summarize_ach_file",
    "validate_ach_file",
]
