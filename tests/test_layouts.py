"""Tests for packaged ACH record layouts."""

from dataclasses import replace

import pytest

from achlens.core.layouts import (
    RecordLayout,
    default_layouts,
    load_layouts,
    validate_layout_contiguity,
)


def test_default_layouts_load_and_cover_94_positions() -> None:
    layouts = default_layouts()

    assert layouts
    assert all(layout.fields[-1].end == 94 for layout in layouts.values())
    assert all(len(layout.fields) > 0 for layout in layouts.values())


def test_load_layouts_rejects_gap(tmp_path) -> None:
    path = tmp_path / "gap.yaml"
    path.write_text(
        "records:\n  broken:\n"
        "  - {name: first, start: 1, end: 10, length: 10, type: N, required: true}\n"
        "  - {name: second, start: 12, end: 94, length: 83, type: AN, required: false}\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="gap"):
        load_layouts(path)


def test_load_layouts_rejects_overlap(tmp_path) -> None:
    path = tmp_path / "overlap.yaml"
    path.write_text(
        "records:\n  broken:\n"
        "  - {name: first, start: 1, end: 10, length: 10, type: N, required: true}\n"
        "  - {name: second, start: 10, end: 94, length: 85, type: AN, required: false}\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="overlap"):
        load_layouts(path)


def test_validate_layout_rejects_out_of_range_field() -> None:
    layout = RecordLayout(
        name="broken",
        fields=(
            replace(
                default_layouts()["file_header"].fields[0],
                start=0,
                end=0,
            ),
        ),
    )

    with pytest.raises(ValueError, match="out of range"):
        validate_layout_contiguity(layout)