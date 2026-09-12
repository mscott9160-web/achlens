"""Benchmark validation of a large deterministic synthetic ACH file.

Usage:
    python scripts/benchmark_validation.py --entries 100000
"""

from __future__ import annotations

import argparse
import platform
import time
import tracemalloc

from achlens.core import generate_ach_file, validate


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--entries", type=int, default=100_000)
    parser.add_argument("--seed", type=int, default=20260912)
    parser.add_argument(
        "--max-validation-seconds",
        type=float,
        help="fail if plain validation wall-clock time exceeds this value",
    )
    parser.add_argument(
        "--max-peak-megabytes",
        type=float,
        help="fail if the tracemalloc peak exceeds this value",
    )
    parser.add_argument(
        "--no-memory-measurement",
        action="store_true",
        help="skip the separate tracemalloc validation run",
    )
    args = parser.parse_args()
    if args.entries < 1:
        parser.error("--entries must be positive")
    if args.max_validation_seconds is not None and args.max_validation_seconds < 0:
        parser.error("--max-validation-seconds must not be negative")
    if args.max_peak_megabytes is not None and args.max_peak_megabytes < 0:
        parser.error("--max-peak-megabytes must not be negative")
    if args.max_peak_megabytes is not None and args.no_memory_measurement:
        parser.error("--max-peak-megabytes requires memory measurement")

    batches = (args.entries + 9_999) // 10_000
    entries_per_batch = (args.entries + batches - 1) // batches
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
    peak_megabytes: float | None = None
    if not args.no_memory_measurement:
        tracemalloc.start()
        validate(content)
        _, peak_bytes = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        peak_megabytes = peak_bytes / 1_000_000

    print(f"entries_requested={args.entries}")
    print(f"records={len(content.splitlines())}")
    print(f"python_version={platform.python_version()}")
    print(f"platform={platform.platform()}")
    print(f"generation_seconds={generation_seconds:.3f}")
    print(f"validation_seconds={validation_seconds:.3f}")
    if peak_megabytes is None:
        print("validation_memory_measurement=disabled")
    else:
        print("validation_memory_measurement=tracemalloc_separate_run")
        print(f"peak_megabytes={peak_megabytes:.1f}")
    print(f"valid={report.valid}")
    print(f"error_count={report.counts['error']}")

    exceeded: list[str] = []
    if (
        args.max_validation_seconds is not None
        and validation_seconds > args.max_validation_seconds
    ):
        exceeded.append("validation_seconds")
    if args.max_peak_megabytes is not None and peak_megabytes is not None:
        if peak_megabytes > args.max_peak_megabytes:
            exceeded.append("peak_megabytes")
    if exceeded:
        print(f"threshold_exceeded={','.join(exceeded)}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
