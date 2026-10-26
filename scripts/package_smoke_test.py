"""Build and smoke-test the achlens wheel without publishing it."""

from __future__ import annotations

import asyncio
import os
import subprocess
import sys
import tempfile
from pathlib import Path


async def _mcp_protocol_smoke_test(environment: dict[str, str], cwd: Path) -> None:
    from mcp import ClientSession
    from mcp.client.stdio import StdioServerParameters, stdio_client

    parameters = StdioServerParameters(
        command=sys.executable,
        args=["-m", "achlens.cli", "serve"],
        env=environment,
        cwd=cwd,
    )
    async with stdio_client(parameters) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            initialized = await session.initialize()
            if initialized.server_info.name != "achlens":
                raise SystemExit("packaged MCP server did not identify as achlens")
            tools = await session.list_tools()
            if "validate_ach_file" not in {tool.name for tool in tools.tools}:
                raise SystemExit("packaged MCP server did not expose validate_ach_file")
            status = await session.call_tool("server_status", {})
            if status.structured_content != {
                "name": "achlens",
                "status": "ready",
                "transport": "stdio",
            }:
                raise SystemExit("packaged MCP server returned an unexpected status")


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    subprocess.run(
        [sys.executable, "-m", "build", "--wheel", "--outdir", str(root / "dist")],
        cwd=root,
        check=True,
    )
    wheel = max((root / "dist").glob("*.whl"), key=lambda path: path.stat().st_mtime)
    with tempfile.TemporaryDirectory(prefix="achlens-package-") as target:
        subprocess.run(
            [
                sys.executable,
                "-m",
                "pip",
                "install",
                "--quiet",
                "--target",
                target,
                str(wheel),
            ],
            check=True,
        )
        environment = os.environ.copy()
        environment["PYTHONPATH"] = target
        help_result = subprocess.run(
            [sys.executable, "-m", "achlens.cli", "--help"],
            env=environment,
            cwd=target,
            capture_output=True,
            text=True,
            check=True,
        )
        if "validate" not in help_result.stdout or "serve" not in help_result.stdout:
            raise SystemExit("package CLI smoke test did not expose expected commands")
        asyncio.run(_mcp_protocol_smoke_test(environment, Path(target)))
    print(f"Package smoke test passed: {wheel.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
