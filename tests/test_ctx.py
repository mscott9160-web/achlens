"""Initial CTX support coverage."""

from achlens.core import generate_ach_file, parse, validate


def test_ctx_uses_corporate_entry_layout() -> None:
    content = generate_ach_file(
        sec_code="CTX",
        entries_per_batch=2,
        include_addenda=True,
        seed=13,
        effective_date="260912",
    )
    parsed = parse(content)
    assert (
        parsed.batches[0].header.fields["standard_entry_class_code"].raw.strip()
        == "CTX"
    )
    assert parsed.batches[0].entries[0].detail.layout == "entry_detail_ccd"
    assert len(parsed.batches[0].entries[0].addenda) == 2
    assert (
        parsed.batches[0].entries[0].addenda[1].fields["addenda_sequence_number"].raw
        == "0002"
    )
    assert validate(content).valid


def test_ctx_is_recognized_but_remains_structurally_scoped() -> None:
    content = generate_ach_file(sec_code="CTX", seed=13, effective_date="260912")
    report = validate(content)
    assert report.counts_by_rule.get("BH004", 0) == 1
    assert report.valid
