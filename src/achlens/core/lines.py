"""Split ACH text into records without interpreting record fields."""

from dataclasses import dataclass, field
from enum import StrEnum


class LineEnding(StrEnum):
    """Line-ending styles found in an ACH input."""

    LF = "lf"
    CRLF = "crlf"
    MIXED = "mixed"
    NONE = "none"


class RecordLength(StrEnum):
    """Length status for a raw ACH record."""

    EXACT = "exact"
    SHORT = "short"
    OVERLONG = "overlong"


@dataclass(frozen=True, init=False)
class LineRecord:
    """One input record, retaining its source text and terminator.

    ``potential_trailing_space_loss`` identifies a short record that may have
    omitted trailing spaces. It is a candidate for later validation, not proof
    that the omitted tail was blank.
    """

    line_number: int
    raw: str
    ending: str
    length: RecordLength
    potential_trailing_space_loss: bool
    _content: str = field(repr=False, compare=False)

    def __init__(
        self,
        line_number: int,
        raw: str,
        ending: str,
        length: RecordLength,
        potential_trailing_space_loss: bool,
        *,
        _content: str | None = None,
    ) -> None:
        object.__setattr__(self, "line_number", line_number)
        object.__setattr__(self, "raw", raw)
        object.__setattr__(self, "ending", ending)
        object.__setattr__(self, "length", length)
        object.__setattr__(
            self, "potential_trailing_space_loss", potential_trailing_space_loss
        )
        object.__setattr__(
            self,
            "_content",
            (
                _content
                if _content is not None
                else raw[: -len(ending)]
                if ending
                else raw
            ),
        )

    @property
    def content(self) -> str:
        """Return the record without its line terminator."""
        return self._content


@dataclass(frozen=True)
class SplitLines:
    """The records and line-ending summary produced from ACH text."""

    records: tuple[LineRecord, ...]
    line_ending: LineEnding


def _ending_kind(endings: tuple[str, ...]) -> LineEnding:
    kinds = set(endings)
    if not kinds:
        return LineEnding.NONE
    if kinds == {"\n"}:
        return LineEnding.LF
    if kinds == {"\r\n"}:
        return LineEnding.CRLF
    return LineEnding.MIXED


def split_lines(text: str) -> SplitLines:
    """Split *text* into records while preserving raw content and endings.

    LF and CRLF are supported. An unterminated final record is retained; an
    empty input produces no records. Lone carriage returns are rejected.
    """
    if "\r" in text.replace("\r\n", ""):
        raise ValueError("unsupported line ending: expected LF or CRLF")

    records: list[LineRecord] = []
    endings: list[str] = []
    start = 0
    line_number = 1
    while start < len(text):
        newline = text.find("\n", start)
        if newline == -1:
            raw = text[start:]
            ending = ""
            start = len(text)
        else:
            ending = "\r\n" if newline > start and text[newline - 1] == "\r" else "\n"
            raw_end = newline - 1 if ending == "\r\n" else newline
            raw = text[start:raw_end] + ending
            endings.append(ending)
            start = newline + 1

        content = raw[: -len(ending)] if ending else raw
        if len(content) < 94:
            length = RecordLength.SHORT
            potential_trailing_space_loss = True
        elif len(content) > 94:
            length = RecordLength.OVERLONG
            potential_trailing_space_loss = False
        else:
            length = RecordLength.EXACT
            potential_trailing_space_loss = False
        records.append(
            LineRecord(
                line_number,
                raw,
                ending,
                length,
                potential_trailing_space_loss,
                _content=content,
            )
        )
        line_number += 1

    return SplitLines(tuple(records), _ending_kind(tuple(endings)))
