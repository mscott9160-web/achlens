"""Command-line entry point for achlens."""

import json
from pathlib import Path

import typer

app = typer.Typer(
    name="achlens",
    help="Local-first tools for synthetic ACH file development.",
    no_args_is_help=True,
)


@app.callback()
def cli_callback() -> None:
    """Run the achlens command-line interface."""


@app.command()
def serve() -> None:
    """Run the MCP server over stdio."""
    from achlens.server.app import run

    run()


def _emit(result: dict[str, object]) -> None:
    typer.echo(json.dumps(result, indent=2, sort_keys=True))


@app.command()
def validate(
    path: Path = typer.Argument(..., exists=True, dir_okay=False),
    min_severity: str = typer.Option("info", "--min-severity"),
) -> None:
    """Validate an ACH file and exit 1 when errors are found."""
    from achlens.server.tools import validate_ach_file

    result = validate_ach_file(
        content=path.read_text(encoding="utf-8"),
        min_severity=min_severity,  # type: ignore[arg-type]
    )
    _emit(result)
    if result.get("valid") is not True:
        raise typer.Exit(code=1)


@app.command()
def summarize(path: Path = typer.Argument(..., exists=True, dir_okay=False)) -> None:
    """Print an ACH file summary as JSON."""
    from achlens.server.tools import summarize_ach_file

    _emit(summarize_ach_file(content=path.read_text(encoding="utf-8")))


@app.command()
def generate(
    sec: str = typer.Option("PPD", "--sec"),
    entries: int = typer.Option(5, "--entries"),
    batches: int = typer.Option(1, "--batches"),
    service_class: int = typer.Option(200, "--service-class"),
    seed: int | None = typer.Option(None, "--seed"),
) -> None:
    """Generate a synthetic ACH file to standard output."""
    from achlens.server.tools import generate_test_ach_file

    result = generate_test_ach_file(
        sec_code=sec,  # type: ignore[arg-type]
        entries_per_batch=entries,
        batches=batches,
        service_class=service_class,  # type: ignore[arg-type]
        seed=seed,
    )
    if "error" in result:
        _emit(result)
        raise typer.Exit(code=1)
    typer.echo(str(result["content"]))


@app.command()
def repair(path: Path = typer.Argument(..., exists=True, dir_okay=False)) -> None:
    """Repair an ACH file and write a new repaired file beside it."""
    from achlens.core.repair import repair_control_records

    result = repair_control_records(path.read_text(encoding="utf-8"))
    if result.refused:
        _emit({"error": {"code": "REPAIR_UNSAFE", "message": result.refusal_reason}})
        raise typer.Exit(code=1)
    output = path.with_name(f"{path.stem}.repaired{path.suffix}")
    if output.exists():
        _emit({"error": {"code": "OUTPUT_EXISTS", "message": str(output)}})
        raise typer.Exit(code=1)
    output.write_text(result.repaired_content or "", encoding="utf-8")
    _emit(
        {
            "path": str(output),
            "changes": [change.__dict__ for change in result.changes],
            "valid": result.valid,
        }
    )
    if not result.valid:
        raise typer.Exit(code=1)


def main() -> None:
    """Launch the Typer application."""
    app()


if __name__ == "__main__":
    main()
