"""Compare achlens with an externally configured ACH validator.

The external command must accept one ACH file path and print JSON containing a
boolean ``valid`` key. Configure ``ACHLENS_DIFFERENTIAL_COMMAND`` as a command
prefix, for example ``validator --file``. The file path is appended.

When the command is unset, this script exits successfully with a skip message.
"""

from __future__ import annotations

import json
import os
import shlex
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

from achlens.core import generate_ach_file, validate


@dataclass(frozen=True)
class DifferentialCase:
    rule: str
    mutation: str
    case: int
    options: dict[str, list[str]]

    @property
    def name(self) -> str:
        prefix = "valid" if self.rule == "none" else f"bad_{self.mutation}"
        return f"{prefix}-{self.case:03d}"


def build_cases() -> tuple[DifferentialCase, ...]:
    mutations = (
        ("none", "baseline", {}),
        ("ED004", "check_digit", {"inject_errors": ["ED004"]}),
        ("BC002", "batch_count", {"inject_errors": ["BC002"]}),
        ("FC004", "file_hash", {"inject_errors": ["FC004"]}),
        ("S011", "padding", {"inject_errors": ["S011"]}),
    )
    return tuple(
        DifferentialCase(rule, mutation, case, options)
        for case in range(1, 21)
        for rule, mutation, options in mutations
    )


_CASES = build_cases()


def main(argv: Sequence[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact", type=Path)
    arguments = parser.parse_args([] if argv is None else argv)
    command_text = os.environ.get("ACHLENS_DIFFERENTIAL_COMMAND")
    if not command_text:
        print("SKIP: ACHLENS_DIFFERENTIAL_COMMAND is not configured")
        return 0
    command = shlex.split(command_text)
    disagreements: list[dict[str, object]] = []
    with tempfile.TemporaryDirectory(prefix="achlens-differential-") as directory:
        root = Path(directory)
        for differential_case in _CASES:
            content = generate_ach_file(
                seed=20260912 + differential_case.case,
                effective_date="260912",
                **differential_case.options,
            )
            expected = validate(content).valid
            path = root / f"{differential_case.name}.ach"
            path.write_text(content, encoding="ascii")
            completed = subprocess.run(
                [*command, str(path)],
                capture_output=True,
                text=True,
                check=False,
            )
            if completed.returncode != 0:
                disagreements.append(
                    {
                        "rule": differential_case.rule,
                        "mutation": differential_case.mutation,
                        "case": differential_case.case,
                        "triage_status": "untriaged",
                        "detail": f"external command exited {completed.returncode}",
                    }
                )
                continue
            try:
                actual = bool(json.loads(completed.stdout)["valid"])
            except (KeyError, json.JSONDecodeError) as error:
                disagreements.append(
                    {
                        "rule": differential_case.rule,
                        "mutation": differential_case.mutation,
                        "case": differential_case.case,
                        "triage_status": "untriaged",
                        "detail": f"invalid external JSON ({error})",
                    }
                )
                continue
            if actual != expected:
                disagreements.append(
                    {
                        "rule": differential_case.rule,
                        "mutation": differential_case.mutation,
                        "case": differential_case.case,
                        "triage_status": "untriaged",
                        "detail": f"achlens={expected}, external={actual}",
                    }
                )
    if arguments.artifact:
        arguments.artifact.parent.mkdir(parents=True, exist_ok=True)
        arguments.artifact.write_text(
            json.dumps(
                {"case_count": len(_CASES), "disagreements": disagreements}, indent=2
            )
            + "\n",
            encoding="utf-8",
        )
    if disagreements:
        print("Differential disagreements:")
        print(json.dumps(disagreements, indent=2))
        return 1
    print(f"Differential agreement: {len(_CASES)} synthetic cases")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
