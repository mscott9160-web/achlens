"""VPR-02 validation snapshot tests."""

from achlens.core import generate_ach_file, parse
from achlens.core.calculators import batch_totals, file_entry_hash, file_totals
from achlens.core.validation_snapshot import build_validation_snapshot


def test_snapshot_preserves_lines_and_aggregates() -> None:
    content = generate_ach_file(
        batches=2,
        entries_per_batch=2,
        include_addenda=True,
        seed=12,
        effective_date="260912",
    )
    snapshot = build_validation_snapshot(content)
    assert snapshot.line_count == len(content.splitlines())
    assert len(snapshot.batches) == 2
    assert sum(len(batch.entries) for batch in snapshot.batches) == 4
    assert snapshot.file_aggregates.entry_addenda_count == 8
    assert snapshot.file_aggregates.total_credit_cents >= 0
    assert snapshot.file_control is not None


def test_snapshot_preserves_short_line_diagnostics() -> None:
    content = generate_ach_file(seed=12, effective_date="260912")
    lines = content.splitlines()
    lines[0] = lines[0].rstrip()
    snapshot = build_validation_snapshot("\n".join(lines))
    assert snapshot.lines[0].length.value == "short"
    assert snapshot.lines[0].potential_trailing_space_loss


def test_snapshot_aggregates_match_full_parser() -> None:
    content = generate_ach_file(
        batches=3,
        entries_per_batch=3,
        include_addenda=True,
        seed=21,
        effective_date="260912",
    )
    snapshot = build_validation_snapshot(content)
    parsed = parse(content)
    assert snapshot.file_aggregates.entry_hash == file_entry_hash(parsed)
    debit, credit = file_totals(parsed)
    assert snapshot.file_aggregates.total_debit_cents == debit
    assert snapshot.file_aggregates.total_credit_cents == credit
    for snapshot_batch, parsed_batch in zip(snapshot.batches, parsed.batches):
        parsed_debit, parsed_credit = batch_totals(parsed_batch)
        assert snapshot_batch.aggregates.total_debit_cents == parsed_debit
        assert snapshot_batch.aggregates.total_credit_cents == parsed_credit
        assert len(snapshot_batch.entries) == len(parsed_batch.entries)
        assert all(
            left.trace_number == right.detail.fields["trace_number"].raw
            for left, right in zip(snapshot_batch.entries, parsed_batch.entries)
        )


def test_snapshot_parity_corpus_covers_supported_mutations() -> None:
    mutations = (
        [],
        ["S001"],
        ["S011"],
        ["ED004"],
        ["ED012"],
        ["BC002"],
        ["BC003"],
        ["BC004"],
        ["BC005"],
        ["FC001"],
        ["FC003"],
        ["FC004"],
        ["FC005"],
        ["FC006"],
    )
    for seed in range(5):
        for inject_errors in mutations:
            content = generate_ach_file(
                batches=2,
                entries_per_batch=3,
                include_addenda=True,
                seed=seed,
                effective_date="260912",
                inject_errors=list(inject_errors),
            )
            snapshot = build_validation_snapshot(content)
            parsed = parse(content)
            debit, credit = file_totals(parsed)
            assert snapshot.file_aggregates.entry_hash == file_entry_hash(parsed)
            assert snapshot.file_aggregates.total_debit_cents == debit
            assert snapshot.file_aggregates.total_credit_cents == credit
            assert snapshot.file_aggregates.entry_addenda_count == sum(
                len(batch.entries) + sum(len(entry.addenda) for entry in batch.entries)
                for batch in parsed.batches
            )
