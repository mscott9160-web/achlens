"""Regenerate committed synthetic golden fixtures."""

from pathlib import Path

from .builders import valid_file

GOLDEN = Path(__file__).parent / "golden"


def main() -> None:
    GOLDEN.mkdir(exist_ok=True)
    (GOLDEN / "sample_valid.ach").write_text(valid_file(), encoding="ascii")


if __name__ == "__main__":
    main()
