"""CORE-15 synthetic generator tests."""

import pytest

from achlens.core import generate_ach_file, parse, validate


def test_seeded_generation_is_repeatable_and_valid() -> None:
    first = generate_ach_file(seed=7, entries_per_batch=3, effective_date="260911")
    second = generate_ach_file(seed=7, entries_per_batch=3, effective_date="260911")
    assert first == second
    assert all(len(line) == 94 for line in first.splitlines())
    assert validate(first).valid


def test_generator_supports_sec_codes_and_service_classes() -> None:
    for sec_code in ("PPD", "CCD", "WEB"):
        for service_class in (200, 220, 225):
            content = generate_ach_file(
                sec_code=sec_code,
                service_class=service_class,
                entries_per_batch=2,
                seed=3,
                effective_date="260911",
            )
            assert validate(content).valid


def test_generator_supports_prenotes_addenda_and_multiple_batches() -> None:
    content = generate_ach_file(
        batches=2,
        entries_per_batch=2,
        include_prenotes=True,
        include_addenda=True,
        seed=11,
        effective_date="260911",
    )
    parsed = parse(content)
    assert len(parsed.batches) == 2
    assert (
        sum(len(entry.addenda) for batch in parsed.batches for entry in batch.entries)
        == 4
    )
    assert validate(content).valid


def test_generator_rejects_invalid_options() -> None:
    with pytest.raises(ValueError):
        generate_ach_file(sec_code="IAT")
    with pytest.raises(ValueError):
        generate_ach_file(batches=0)
    with pytest.raises(ValueError):
        generate_ach_file(entries_per_batch=10_001)
    with pytest.raises(ValueError):
        generate_ach_file(effective_date="not-a-date")


@pytest.mark.parametrize("rule_id", ["S001", "S011", "ED004", "BC002", "FC001"])
def test_generator_injects_supported_errors(rule_id: str) -> None:
    content = generate_ach_file(
        entries_per_batch=2,
        seed=5,
        effective_date="260911",
        inject_errors=[rule_id],
    )
    assert not validate(content).valid


def test_generator_injects_entry_and_addenda_errors() -> None:
    entry_error = generate_ach_file(
        entries_per_batch=2,
        seed=5,
        effective_date="260911",
        include_prenotes=True,
        inject_errors=["ED007", "ED012"],
    )
    assert {finding.rule_id for finding in validate(entry_error).findings} >= {
        "ED007",
        "ED012",
    }
    addenda_error = generate_ach_file(
        seed=5,
        effective_date="260911",
        include_addenda=True,
        inject_errors=["AD004"],
    )
    assert "AD004" in validate(addenda_error).counts_by_rule


def test_generator_rejects_unknown_injection() -> None:
    with pytest.raises(ValueError, match="unsupported error injection"):
        generate_ach_file(inject_errors=["NOPE"])
