"""Tests for the optional differential harness contract."""

import json
import sys
from pathlib import Path

from scripts.differential_validation import build_cases, main


def test_differential_corpus_is_deterministic_and_at_least_100_cases() -> None:
    cases = build_cases()
    assert len(cases) >= 100
    assert cases == build_cases()


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


def test_differential_harness_reports_structured_disagreement(
    monkeypatch, tmp_path: Path
) -> None:
    validator = tmp_path / "validator.py"
    _write_fake_validator(validator, disagree=True)
    monkeypatch.setenv(
        "ACHLENS_DIFFERENTIAL_COMMAND",
        f'"{sys.executable}" "{validator}"',
    )
    artifact = tmp_path / "disagreements.json"
    assert main(["--artifact", str(artifact)]) == 1
    report = json.loads(artifact.read_text(encoding="utf-8"))
    assert report["case_count"] == 100
    assert report["disagreements"][0].keys() >= {
        "rule",
        "mutation",
        "case",
        "triage_status",
    }
    assert report["disagreements"][0]["triage_status"] == "untriaged"


def test_differential_harness_skips_without_external_command(
    monkeypatch, capsys
) -> None:
    monkeypatch.delenv("ACHLENS_DIFFERENTIAL_COMMAND", raising=False)
    assert main() == 0
    assert "SKIP:" in capsys.readouterr().out
