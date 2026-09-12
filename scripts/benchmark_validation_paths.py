"""Compare full-parser and snapshot-adapted validation paths.

Usage:
    python scripts/benchmark_validation_paths.py --entries 100000
"""

from __future__ import annotations

import argparse
import time

from achlens.core import generate_ach_file, validate
from achlens.core.validation_snapshot import (
    build_validation_snapshot,
    validation_context_from_snapshot,
)
from achlens.core.validator import validate as validate_context


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--entries", type=int, default=100_000)
    args = parser.parse_args()
    batches = (args.entries + 9_999) // 10_000
    entries_per_batch = (args.entries + batches - 1) // batches
    content = generate_ach_file(
        batches=batches,
        entries_per_batch=entries_per_batch,
        seed=20260912,
        effective_date="260912",
    )

    start = time.perf_counter()
    full = validate(content)
    full_seconds = time.perf_counter() - start

    start = time.perf_counter()
    snapshot = build_validation_snapshot(content)
    adapted = validate_context(validation_context_from_snapshot(content, snapshot))
    snapshot_seconds = time.perf_counter() - start

    print(f"entries={args.entries}")
    print(f"full_validation_seconds={full_seconds:.3f}")
    print(f"snapshot_adapter_validation_seconds={snapshot_seconds:.3f}")
    print(f"full_valid={full.valid}")
    print(f"snapshot_valid={adapted.valid}")
    print(f"findings_equal={full.findings == adapted.findings}")
    print(f"counts_equal={full.counts == adapted.counts}")


if __name__ == "__main__":
    main()
