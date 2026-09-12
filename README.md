# achlens

<!-- mcp-name: io.github.mscott9160-web/achlens -->

achlens is a local-first Python MCP server and CLI for inspecting synthetic ACH
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

The MCP server exposes validation, summaries, parsed-record paging, control
explanations, routing checks, code lookup, synthetic generation, and control
repair. See [docs/tools.md](docs/tools.md) for the current tool surface.

Sensitive fields are masked by default. Configure `ACHLENS_ALLOWED_ROOTS` to
enable MCP path inputs; otherwise provide file content directly. See
[SECURITY.md](SECURITY.md) for the data and write boundaries.

Synthetic generator output and repaired content are raw fixed-width ACH paths,
so they remain structurally valid and are marked synthetic where applicable.
Do not log or serialize these raw strings through structured summaries; use the
masked parsed, summarized, and diff outputs for reporting.

## Development

This project uses [uv](https://docs.astral.sh/uv/).

```text
uv sync
uv run achlens --help
uv run pytest -q
uv run ruff check .
uv run ruff format --check .
uv run mypy --strict src
```

Never add real payment data, account numbers, or ACH files to this repository.
