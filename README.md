# Achlens

[![PyPI](https://img.shields.io/pypi/v/achlens)](https://pypi.org/project/achlens/)
[![Python](https://img.shields.io/pypi/pyversions/achlens)](https://pypi.org/project/achlens/)
[![License](https://img.shields.io/pypi/l/achlens)](https://github.com/mscott9160-web/achlens/blob/master/LICENSE)
[![CI](https://github.com/mscott9160-web/achlens/actions/workflows/ci.yml/badge.svg)](https://github.com/mscott9160-web/achlens/actions/workflows/ci.yml)

<!-- mcp-name: io.github.mscott9160-web/achlens -->

Achlens is a local-first Python MCP server and CLI for inspecting synthetic ACH
files. It parses fixed-width records, validates structure and control totals,
explains findings, masks sensitive fields, repairs derived controls, and
generates deterministic test files. It never transmits ACH files or makes
bank/network calls.

Use synthetic data only. This project is not a bank gateway, compliance
advisor, or transmission system.

## Quick Start

```text
uv sync
uv run achlens --help
uv run achlens validate tests/fixtures/golden/sample_valid.ach
uv run achlens generate --sec PPD --entries 5 --seed 7 > synthetic.ach
```

In Windows PowerShell, use an explicit ASCII encoding because PowerShell's
default `>` redirection can write UTF-16 output that is not valid ACH text:

```powershell
uvx achlens generate --sec PPD --entries 5 --seed 7 |
	Set-Content -Encoding ascii synthetic.ach
```

Run the MCP server over stdio:

```text
uv run achlens serve
```

## MCP Client Setup

Install the published package with `uvx`; it starts the server locally over
stdio and does not transmit ACH files.

### VS Code and Copilot

Create `.vscode/mcp.json` in your workspace:

```json
{
  "servers": {
    "achlens": {
      "type": "stdio",
      "command": "uvx",
      "args": ["achlens"]
    }
  }
}
```

### Claude Desktop

Add the following entry to the `mcpServers` object in Claude Desktop's MCP
configuration:

```json
{
  "achlens": {
    "command": "uvx",
    "args": ["achlens"]
  }
}
```

By default, MCP tools accept ACH content directly but cannot read local paths.
To allow read-only access to a specific directory, set
`ACHLENS_ALLOWED_ROOTS` in the server environment to that directory. Use
synthetic ACH data only.

The MCP server exposes validation, summaries, parsed-record paging, control
explanations, routing checks, code lookup, synthetic generation, and control
repair. See [docs/tools.md](docs/tools.md) for the current tool surface.

Sensitive fields are masked by default. Configure `ACHLENS_ALLOWED_ROOTS` to
enable MCP path inputs; otherwise provide file content directly. See
[SECURITY.md](SECURITY.md) for the data and write boundaries.

## Development

This project uses [uv](https://docs.astral.sh/uv/).

```text
uv sync
uv run achlens --help
PYTHONPATH=. uv run pytest -q
uv run ruff check .
uv run ruff format --check .
uv run mypy --strict src
```

## Without uv

The CLI and test suite also work with plain pip:

```text
pip install -e . pytest
achlens --help
achlens validate tests/fixtures/golden/sample_valid.ach
achlens generate --sec PPD --entries 5 --seed 7
PYTHONPATH=. pytest
```

Set `PYTHONPATH=.` from the repository root when running tests so fixture and
script imports resolve. In Windows PowerShell, use
`$env:PYTHONPATH = "."; pytest`.

Never add real payment data, account numbers, or ACH files to this repository.
