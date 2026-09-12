"""Initial CTX support coverage."""

import pytest

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


def test_ctx_addenda_count_is_configurable_and_bounded() -> None:
    content = generate_ach_file(
        sec_code="CTX",
        entries_per_batch=1,
        include_addenda=True,
        addenda_per_entry=3,
        seed=14,
        effective_date="260912",
    )
    parsed = parse(content)
    assert len(parsed.batches[0].entries[0].addenda) == 3
    assert validate(content).valid

    with pytest.raises(ValueError):
        generate_ach_file(sec_code="CTX", addenda_per_entry=10_000)
    with pytest.raises(ValueError):
        generate_ach_file(sec_code="PPD", addenda_per_entry=2)
