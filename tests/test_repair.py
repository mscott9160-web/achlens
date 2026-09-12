"""CORE-17 control repair tests."""

from achlens.core import generate_ach_file, repair_control_records, validate


def test_repair_restores_control_mutations() -> None:
    original = generate_ach_file(
        entries_per_batch=2,
        include_addenda=True,
        seed=4,
        effective_date="260911",
    )
    broken = generate_ach_file(
        entries_per_batch=2,
        include_addenda=True,
        seed=4,
        effective_date="260911",
        inject_errors=[
            "BC002",
            "BC003",
            "BC004",
            "BC005",
            "FC001",
            "FC003",
            "FC004",
            "FC005",
            "FC006",
        ],
    )
    assert not validate(broken).valid
    result = repair_control_records(broken)
    assert not result.refused
    assert result.repaired_content is not None
    assert result.valid
    assert len(result.changes) >= 9
    assert validate(result.repaired_content).valid
    assert original == result.repaired_content


def test_repair_refuses_unsafe_record_order() -> None:
    content = generate_ach_file(seed=4, effective_date="260911")
    lines = content.splitlines()
    lines[1], lines[2] = lines[2], lines[1]
    result = repair_control_records("\n".join(lines))
    assert result.refused
    assert result.repaired_content is None
    assert "REPAIR_UNSAFE" in (result.refusal_reason or "")


def test_repair_can_restore_short_record_tail() -> None:
    content = generate_ach_file(seed=4, effective_date="260911")
    lines = content.splitlines()
    lines[0] = lines[0].rstrip()
    result = repair_control_records("\n".join(lines))
    assert not result.refused
    assert result.repaired_content is not None
    assert len(result.repaired_content.splitlines()[0]) == 94
