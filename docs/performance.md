# Performance Benchmark

Run the deterministic validation benchmark with:

```text
python scripts/benchmark_validation.py --entries 100000
```

Optional release or scheduled-job gates can be enabled explicitly:

```text
python scripts/benchmark_validation.py --entries 100000 \
	--max-validation-seconds 2 --max-peak-megabytes 500
```

Either threshold returns exit status `1` when exceeded. Thresholds are not
enabled by default. Use `--no-memory-measurement` for a wall-clock-only run;
the default `tracemalloc` measurement is a separate validation run and is not
included in `validation_seconds`.

The benchmark reports:

- physical record count
- generation time
- validation time
- Python version and platform
- plain validation wall-clock time
- peak Python allocation measured by a separate `tracemalloc` run
- validity and error count

The v1 target is validation of 100,000 entries in under two seconds and under
500 MB on a laptop. Benchmark results depend on Python version, operating
system, and hardware, so record the environment with any published result.
The benchmark is intentionally opt-in and is not part of the ordinary unit-test
job.

The snapshot-adapter comparison can be run with:

```text
python scripts/benchmark_validation_paths.py --entries 100000
```

The current comparison is a correctness scaffold, not an optimization result:

```text
full_validation_seconds=6.153
snapshot_adapter_validation_seconds=11.011
findings_equal=True
counts_equal=True
```

The adapter is slower because it reconstructs the existing rule-facing model.
The production validator therefore remains on the full-parser path until a
direct snapshot-native rule implementation avoids that reconstruction cost.

## Baseline and Current Result

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

The memory target is currently within the stated limit, but validation remains
above the two-second target. A wall-clock-only run after the entry-rule lookup
optimization measured `4.434s` for the same 100,000-entry workload. The earlier
`23.645s` figure included tracemalloc overhead and should not be used as the
wall-clock target. Profiling identifies parser field/model construction as the
dominant remaining hotspot; the benchmark remains the acceptance check.

The completed streaming validation suite passed with 193 tests and 1 skipped.
Hosted Windows, Ubuntu, and macOS benchmark runs each completed in under one
second, used 53.8 MB, produced a valid report with no errors, and matched the
legacy path exactly. These parity and cross-platform benchmark criteria pass,
so optimized streaming is enabled by default; the internal
`ACHLENS_DISABLE_STREAMING_VALIDATION=1` switch remains available for rollback.

## Repeated Streaming Comparison

Measured on 2026-09-12 on Windows with Python 3.12 using the repeated
100,000-entry workload:

```text
legacy_runs=5.947,5.424,5.724,5.572,6.807
streaming_runs=6.057,5.842,6.046,5.867,6.397
legacy_median=5.724
streaming_median=6.046
parity=True
records=100030
```

The combined opt-in streaming path is not yet a performance improvement: its
median validation time was 0.322 seconds slower than the legacy path. It
remains opt-in while further optimization and validation work continues.

Post-optimization repeated evidence, measured on 2026-09-12 on Windows with
Python 3.12 using five paired 100,000-entry runs:

```text
paired_runs=5
legacy_median=5.728
streaming_median=2.836
median_improvement=50.5%
validation_reports_matched_exactly=True
records=100030
```

Streaming is now the default built-in validation path. Custom rule runners
continue to use the legacy context path for compatibility.

## Official Optimized Streaming Benchmark

The latest five official optimized streaming CLI benchmarks were measured on
2026-09-12 on Windows with Python 3.12 for the 100,000-entry workload. Memory
measurement was disabled:

```text
optimized_streaming_cli_runs=1.962,2.532,1.916,1.983,2.004
median_validation_seconds=1.983
min_validation_seconds=1.916
max_validation_seconds=2.532
passes_under_2_seconds=3/5
validation_memory_measurement=disabled
```

These local runs preceded the final hosted cross-platform gate. The final gate
passed with exact parity and hosted Windows, Ubuntu, and macOS runs each under
one second at 53.8 MB, so streaming is enabled by default.
