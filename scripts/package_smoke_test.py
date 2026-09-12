"""Build and smoke-test the achlens wheel without publishing it."""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
from pathlib import Path


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    subprocess.run(
        [sys.executable, "-m", "build", "--wheel", "--outdir", str(root / "dist")],
        cwd=root,
        check=True,
    )
    wheel = max((root / "dist").glob("*.whl"), key=lambda path: path.stat().st_mtime)
    with tempfile.TemporaryDirectory(prefix="achlens-package-") as target:
        subprocess.run(
            [
                sys.executable,
                "-m",
                "pip",
                "install",
                "--quiet",
                "--target",
                target,
                str(wheel),
            ],
            check=True,
        )
        environment = os.environ.copy()
        environment["PYTHONPATH"] = target
        help_result = subprocess.run(
            [sys.executable, "-m", "achlens.cli", "--help"],
            env=environment,
            capture_output=True,
            text=True,
            check=True,
        )
        if "validate" not in help_result.stdout or "serve" not in help_result.stdout:
            raise SystemExit("package CLI smoke test did not expose expected commands")
    print(f"Package smoke test passed: {wheel.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
