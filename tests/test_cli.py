"""CLI-01 command tests."""

import json
from pathlib import Path

import pytest

pytest.importorskip("typer")
from typer.testing import CliRunner

from achlens.cli import app
from tests.fixtures.builders import valid_file

runner = CliRunner()


def test_cli_help_lists_commands() -> None:
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    for command in ("validate", "summarize", "generate", "repair", "serve"):
        assert command in result.stdout


def test_cli_validate_and_summarize(tmp_path: Path) -> None:
    source = tmp_path / "sample.ach"
    source.write_text(valid_file(), encoding="ascii")
    validated = runner.invoke(app, ["validate", str(source)])
    assert validated.exit_code == 0
    assert json.loads(validated.stdout)["valid"] is True
    summarized = runner.invoke(app, ["summarize", str(source)])
    assert summarized.exit_code == 0
    assert json.loads(summarized.stdout)["summary"]["entry_count"] == 1


def test_cli_generate_and_repair(tmp_path: Path) -> None:
    generated = runner.invoke(app, ["generate", "--entries", "2", "--seed", "3"])
    assert generated.exit_code == 0
    source = tmp_path / "sample.ach"
    source.write_text(generated.stdout, encoding="ascii")
    repaired = runner.invoke(app, ["repair", str(source)])
    assert repaired.exit_code == 0
    assert (tmp_path / "sample.repaired.ach").exists()
