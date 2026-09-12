"""Benchmark validation of a large deterministic synthetic ACH file.

Usage:
    python scripts/benchmark_validation.py --entries 100000
"""

from __future__ import annotations

import argparse
import time
import tracemalloc

from achlens.core import generate_ach_file, validate


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--entries", type=int, default=100_000)
    parser.add_argument("--seed", type=int, default=20260912)
    args = parser.parse_args()
    if args.entries < 1:
        parser.error("--entries must be positive")

    batches = (args.entries + 9_999) // 10_000
    entries_per_batch = (args.entries + batches - 1) // batches
    tracemalloc.start()
    generation_start = time.perf_counter()
    content = generate_ach_file(
        batches=batches,
        entries_per_batch=entries_per_batch,
        service_class=200,
        seed=args.seed,
        effective_date="260912",
    )
    generation_seconds = time.perf_counter() - generation_start
    validation_start = time.perf_counter()
    report = validate(content)
    validation_seconds = time.perf_counter() - validation_start
    _, peak_bytes = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    print(f"entries_requested={args.entries}")
    print(f"records={len(content.splitlines())}")
    print(f"generation_seconds={generation_seconds:.3f}")
    print(f"validation_seconds={validation_seconds:.3f}")
    print(f"peak_megabytes={peak_bytes / 1_000_000:.1f}")
    print(f"valid={report.valid}")
    print(f"error_count={report.counts['error']}")


if __name__ == "__main__":
    main()
