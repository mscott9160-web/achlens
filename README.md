# achlens

achlens is a local-first Python project for inspecting and validating synthetic
ACH files. Sprint 0 contains the repository foundation only; ACH parsing,
validation, MCP tools, and reference data are intentionally not implemented.

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

Use synthetic data only. Never add real payment data, account numbers, or ACH
files to this repository.
