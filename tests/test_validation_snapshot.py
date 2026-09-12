"""VPR-02 validation snapshot tests."""

from achlens.core import generate_ach_file
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
