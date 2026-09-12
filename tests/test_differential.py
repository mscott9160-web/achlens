"""Tests for the optional differential harness contract."""

import sys
from pathlib import Path

from scripts.differential_validation import main


def _write_fake_validator(path: Path, *, disagree: bool = False) -> None:
    expression = "False" if disagree else "('bad_' not in path.name)"
    path.write_text(
        "import json, pathlib, sys\n"
        "path = pathlib.Path(sys.argv[1])\n"
        f"print(json.dumps({{'valid': {expression}}}))\n",
        encoding="utf-8",
    )


def test_differential_harness_agrees_with_fake_external_validator(
    monkeypatch, tmp_path: Path
) -> None:
    validator = tmp_path / "validator.py"
    _write_fake_validator(validator)
    monkeypatch.setenv(
        "ACHLENS_DIFFERENTIAL_COMMAND",
        f'"{sys.executable}" "{validator}"',
    )
    assert main() == 0


def test_differential_harness_reports_disagreement(monkeypatch, tmp_path: Path) -> None:
    validator = tmp_path / "validator.py"
    _write_fake_validator(validator, disagree=True)
    monkeypatch.setenv(
        "ACHLENS_DIFFERENTIAL_COMMAND",
        f'"{sys.executable}" "{validator}"',
    )
    assert main() == 1
