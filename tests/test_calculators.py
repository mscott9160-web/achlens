import pytest

from achlens.core.calculators import (
    aba_check_digit,
    batch_entry_addenda_count,
    batch_entry_hash,
    batch_totals,
    block_count,
    entry_addenda_count,
    file_entry_addenda_count,
    file_entry_hash,
    file_totals,
    integer_field,
    text_field,
    valid_routing_number,
)
from achlens.core.model import AchFile, Batch, Entry, FieldValue, Record


def detail(
    code: int | str | None, rdfi: int | str | None, amount: int | str | None
) -> Record:
    values = {
        "transaction_code": FieldValue("transaction_code", 2, 3, "", code),
        "receiving_dfi_identification": FieldValue(
            "receiving_dfi_identification", 4, 11, "", rdfi
        ),
        "amount": FieldValue("amount", 30, 39, "", amount),
    }
    return Record(1, "6", "test", "", values)


def make_batch(*details: Record, addenda: int = 0) -> Batch:
    entries = [
        Entry(record, [Record(2, "7", "", "") for _ in range(addenda)])
        for record in details
    ]
    return Batch(entries=entries)


def test_routing_check_digit_and_validation() -> None:
    assert aba_check_digit("12345678") == 0
    assert valid_routing_number("12345678")
    assert valid_routing_number("123456780")
    assert not valid_routing_number("123456781")
    assert not valid_routing_number("1234567")


def test_hashes_truncate_and_match_worked_example() -> None:
    first = make_batch(
        detail(22, 23138010, 154321),
        detail(32, 4400003, 98050),
        detail(23, 32407119, 0),
        addenda=1,
    )
    second = make_batch(detail(27, 4400003, 25000))
    ach_file = AchFile(batches=[first, second])

    assert batch_entry_hash(first) == 59945132
    assert batch_entry_hash(second) == 4400003
    assert file_entry_hash(ach_file) == 64345135
    assert (
        batch_entry_hash(
            make_batch(detail(22, 9999999999, 0), detail(22, 9999999999, 0))
        )
        == 9999999998
    )


def test_file_hash_uses_recomputed_batch_hashes() -> None:
    batch = make_batch(detail(22, 12345678, 100))
    batch.control = Record(
        3,
        "8",
        "",
        "",
        {"entry_hash": FieldValue("entry_hash", 20, 29, "", 9999999999)},
    )

    assert file_entry_hash(AchFile(batches=[batch])) == batch_entry_hash(batch)


def test_hash_rejects_malformed_rdfi() -> None:
    with pytest.raises(ValueError, match="receiving_dfi_identification"):
        batch_entry_hash(make_batch(detail(22, "bad", 100)))


def test_counts_include_addenda_and_exclude_other_records() -> None:
    batch = make_batch(detail(22, 1, 0), detail(22, 2, 0))
    batch.entries[0].addenda.append(Record(2, "7", "", ""))
    assert batch_entry_addenda_count(batch) == 3
    assert file_entry_addenda_count(AchFile(batches=[batch])) == 3
    assert (
        entry_addenda_count([batch.entries[0].detail, *batch.entries[0].addenda]) == 2
    )


def test_totals_cover_credit_debit_prenote_and_zero_codes() -> None:
    batch = make_batch(
        detail(22, 1, 100),
        detail(23, 2, 999),
        detail(24, 3, 0),
        detail(27, 4, 250),
        detail(28, 5, 999),
        detail(29, 6, 0),
    )
    assert batch_totals(batch) == (250, 100)
    assert file_totals(AchFile(batches=[batch])) == (250, 100)


@pytest.mark.parametrize("code", [22, 27])
@pytest.mark.parametrize("amount", [None, "bad"])
def test_totals_reject_malformed_amount_for_dollar_entries(
    code: int, amount: object
) -> None:
    with pytest.raises(ValueError, match="amount"):
        batch_totals(make_batch(detail(code, 1, amount)))


def test_totals_ignore_unknown_codes_without_validating_amount() -> None:
    assert batch_totals(make_batch(detail(99, 1, "bad"))) == (0, 0)


def test_totals_allow_invalid_amount_for_prenote_and_zero_dollar_codes() -> None:
    batch = make_batch(detail(23, 1, "bad"), detail(24, 2, None))
    assert batch_totals(batch) == (0, 0)


def test_safe_fields_and_block_edges() -> None:
    record = detail("bad", "bad", "bad")
    assert integer_field(record, "amount") is None
    assert integer_field(None, "amount") is None
    assert text_field(record, "missing") is None
    assert block_count(20) == 2
    assert block_count(11) == 2
    with pytest.raises(ValueError):
        block_count(-1)
    with pytest.raises(ValueError):
        block_count(11, require_multiple=True)
