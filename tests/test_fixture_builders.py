"""QA-01 tests for generated fixtures and mutation helpers."""

from achlens.core.validator import validate
from tests.fixtures.builders import (
    add_padding,
    delete_line,
    drop_padding,
    inject_non_ascii,
    set_field,
    strip_trailing_spaces,
    swap_lines,
    valid_file,
)


def test_valid_fixture_has_only_94_character_records_and_no_errors() -> None:
    content = valid_file()
    assert len(content.splitlines()) == 10
    assert all(len(line) == 94 for line in content.splitlines())
    assert validate(content).valid


def test_field_mutation_uses_layout_positions() -> None:
    mutated = set_field(valid_file(), 3, "entry_detail_ppd", "amount", 999)
    assert mutated.splitlines()[2][29:39] == "0000000999"
    assert not validate(mutated).valid


def test_line_mutators_change_only_requested_structure() -> None:
    content = valid_file()
    assert len(delete_line(content, 10).splitlines()) == 9
    swapped = swap_lines(content, 2, 3)
    assert swapped.splitlines()[1][0] == "6"
    assert swapped.splitlines()[2][0] == "5"
    assert len(drop_padding(content).splitlines()) == 5
    assert len(add_padding(content, 1).splitlines()) == 11


def test_corruption_mutators_are_visible_to_validation() -> None:
    short = strip_trailing_spaces(valid_file().splitlines()[0])
    assert len(short) < 94
    assert not validate("\n".join([short] + valid_file().splitlines()[1:])).valid
    assert not validate(inject_non_ascii(valid_file())).valid
