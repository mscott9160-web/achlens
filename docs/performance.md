# Performance Benchmark

Run the deterministic validation benchmark with:

```text
python scripts/benchmark_validation.py --entries 100000
```

The benchmark reports:

- physical record count
- generation time
- validation time
- peak Python allocation measured by `tracemalloc`
- validity and error count

The v1 target is validation of 100,000 entries in under two seconds and under
500 MB on a laptop. Benchmark results depend on Python version, operating
system, and hardware, so record the environment with any published result.
The benchmark is intentionally opt-in and is not part of the ordinary unit-test
job.

## Baseline

Measured on 2026-09-12 with the current implementation and the configured
Python 3.12 environment:

```text
entries_requested=100000
records=100030
generation_seconds=1.676
validation_seconds=5.015
validation_memory_measurement=tracemalloc
peak_megabytes=270.6
valid=True
error_count=0
```

The memory target is currently within the stated limit, but uninstrumented
validation is above the two-second target. The earlier `23.645s` figure included
`tracemalloc` overhead and should not be used as the wall-clock target. Profiling
identifies parser field construction and repeated entry-rule field access as the
main remaining hotspots. This is a known performance gap for the next
optimization slice; the benchmark remains the acceptance check.
