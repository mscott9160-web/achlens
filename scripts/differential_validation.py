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
import tempfile
from pathlib import Path

from achlens.core import generate_ach_file, validate

_CASES = (
    ("valid", {}),
    ("bad_check_digit", {"inject_errors": ["ED004"]}),
    ("bad_batch_count", {"inject_errors": ["BC002"]}),
    ("bad_file_hash", {"inject_errors": ["FC004"]}),
    ("bad_padding", {"inject_errors": ["S011"]}),
)


def main() -> int:
    command_text = os.environ.get("ACHLENS_DIFFERENTIAL_COMMAND")
    if not command_text:
        print("SKIP: ACHLENS_DIFFERENTIAL_COMMAND is not configured")
        return 0
    command = shlex.split(command_text)
    disagreements: list[str] = []
    with tempfile.TemporaryDirectory(prefix="achlens-differential-") as directory:
        root = Path(directory)
        for name, options in _CASES:
            content = generate_ach_file(
                seed=20260912, effective_date="260912", **options
            )
            expected = validate(content).valid
            path = root / f"{name}.ach"
            path.write_text(content, encoding="ascii")
            completed = subprocess.run(
                [*command, str(path)],
                capture_output=True,
                text=True,
                check=False,
            )
            if completed.returncode != 0:
                disagreements.append(
                    f"{name}: external command exited {completed.returncode}"
                )
                continue
            try:
                actual = bool(json.loads(completed.stdout)["valid"])
            except (KeyError, json.JSONDecodeError) as error:
                disagreements.append(f"{name}: invalid external JSON ({error})")
                continue
            if actual != expected:
                disagreements.append(f"{name}: achlens={expected}, external={actual}")
    if disagreements:
        print("Differential disagreements:")
        print("\n".join(disagreements))
        return 1
    print(f"Differential agreement: {len(_CASES)} synthetic cases")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
