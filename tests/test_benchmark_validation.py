"""Tests for the opt-in validation benchmark gates."""

import importlib.util
import sys
from pathlib import Path

import pytest


@pytest.fixture()
def benchmark(monkeypatch):
    path = Path(__file__).parents[1] / "scripts" / "benchmark_validation.py"
    spec = importlib.util.spec_from_file_location("benchmark_validation", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    monkeypatch.setattr(module, "generate_ach_file", lambda **kwargs: "record\n")
    monkeypatch.setattr(
        module,
        "validate",
        lambda content: type("Report", (), {"valid": True, "counts": {"error": 0}})(),
    )
    return module


def test_default_output_keeps_memory_measurement_and_returns_success(
    benchmark, monkeypatch, capsys
) -> None:
    monkeypatch.setattr(sys, "argv", ["benchmark_validation.py", "--entries", "1"])

    assert benchmark.main() == 0

    output = capsys.readouterr().out
    assert "validation_seconds=" in output
    assert "validation_memory_measurement=tracemalloc_separate_run" in output
    assert "python_version=" in output
    assert "platform=" in output


def test_wall_clock_threshold_returns_nonzero(benchmark, monkeypatch, capsys) -> None:
    monkeypatch.setattr(
        benchmark.time,
        "perf_counter",
        iter([0.0, 0.0, 1.0, 2.0]).__next__,
    )
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "benchmark_validation.py",
            "--entries",
            "1",
            "--max-validation-seconds",
            "0.5",
        ],
    )

    assert benchmark.main() == 1
    assert "threshold_exceeded=validation_seconds" in capsys.readouterr().out


def test_memory_threshold_requires_measurement(benchmark, monkeypatch) -> None:
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "benchmark_validation.py",
            "--entries",
            "1",
            "--max-peak-megabytes",
            "1",
            "--no-memory-measurement",
        ],
    )

    with pytest.raises(SystemExit) as error:
        benchmark.main()

    assert error.value.code == 2


def test_peak_memory_threshold_returns_nonzero(benchmark, monkeypatch, capsys) -> None:
    monkeypatch.setattr(
        sys,
        "argv",
        ["benchmark_validation.py", "--entries", "1", "--max-peak-megabytes", "0"],
    )

    assert benchmark.main() == 1
    assert "threshold_exceeded=peak_megabytes" in capsys.readouterr().out
