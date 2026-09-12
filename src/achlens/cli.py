"""Command-line entry point for achlens."""

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


def main() -> None:
    """Launch the Typer application."""
    app()


if __name__ == "__main__":
    main()
