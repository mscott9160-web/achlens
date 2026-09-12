"""Tests for loss-aware ACH line splitting."""

import pytest

from achlens.core.lines import LineEnding, LineRecord, RecordLength, split_lines


def test_lf_preserves_raw_records_and_numbers() -> None:
    result = split_lines("A" * 94 + "\n" + "B" * 94 + "\n")
    assert result.line_ending is LineEnding.LF
    assert [record.line_number for record in result.records] == [1, 2]
    assert result.records[0].raw == "A" * 94 + "\n"
    assert result.records[0].content == "A" * 94
    assert result.records[0].length is RecordLength.EXACT


def test_crlf_and_final_unterminated_record() -> None:
    result = split_lines("A" * 94 + "\r\n" + "B" * 94)
    assert result.line_ending is LineEnding.CRLF
    assert [record.ending for record in result.records] == ["\r\n", ""]


def test_mixed_endings_are_reported() -> None:
    result = split_lines("A\nB\r\nC")
    assert result.line_ending is LineEnding.MIXED


def test_single_record_without_ending_and_empty_input() -> None:
    assert split_lines("record").line_ending is LineEnding.NONE
    assert len(split_lines("record").records) == 1
    assert split_lines("").records == ()
    assert split_lines("").line_ending is LineEnding.NONE


def test_short_record_is_only_a_candidate_for_trailing_space_loss() -> None:
    record = split_lines("6" + " " * 92).records[0]
    assert record.length is RecordLength.SHORT
    assert record.potential_trailing_space_loss


@pytest.mark.parametrize("content", ["ABC123", "600", "6\t" + " " * 10])
def test_meaningful_short_record_is_not_marked_proven_safe(content: str) -> None:
    record = split_lines(content).records[0]
    assert record.length is RecordLength.SHORT
    assert record.potential_trailing_space_loss


def test_overlong_record_is_not_restorable() -> None:
    record = split_lines("9" * 95).records[0]
    assert record.length is RecordLength.OVERLONG
    assert not record.potential_trailing_space_loss


@pytest.mark.parametrize("ending", ["\n", "\r\n"])
def test_short_record_preserves_meaningful_trailing_spaces_and_ending(
    ending: str,
) -> None:
    content = "ABC123" + " " * 4
    record = split_lines(content + ending).records[0]
    assert record.raw == content + ending
    assert record.content == content
    assert record.ending == ending
    assert record.potential_trailing_space_loss


def test_lone_carriage_return_is_rejected() -> None:
    with pytest.raises(ValueError, match="LF or CRLF"):
        split_lines("A\rB")


@pytest.mark.parametrize(
    ("text", "expected_contents", "expected_endings"),
    [
        ("A\nB\n", ["A", "B"], ["\n", "\n"]),
        ("A\r\nB\r\n", ["A", "B"], ["\r\n", "\r\n"]),
        ("A\nB\r\nC", ["A", "B", "C"], ["\n", "\r\n", ""]),
        ("A" * 94 + "\n" + "B" * 95, ["A" * 94, "B" * 95], ["\n", ""]),
    ],
)
def test_split_records_cache_content_without_changing_line_metadata(
    text: str, expected_contents: list[str], expected_endings: list[str]
) -> None:
    records = split_lines(text).records

    assert [record.content for record in records] == expected_contents
    assert [record.ending for record in records] == expected_endings
    assert [record.raw for record in records] == [
        content + ending for content, ending in zip(expected_contents, expected_endings)
    ]


def test_direct_line_record_construction_derives_content() -> None:
    record = LineRecord(1, "ABC\r\n", "\r\n", RecordLength.SHORT, True)

    assert record.content == "ABC"
