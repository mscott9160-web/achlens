"""Initial v1.1 ACH diff coverage."""

from achlens.core import diff_ach_files, generate_ach_file
from achlens.server.tools import diff_ach_files_tool


def test_diff_equal_and_changed_files() -> None:
    left = generate_ach_file(seed=22, effective_date="260912")
    assert diff_ach_files(left, left)["equal"] is True
    right = generate_ach_file(seed=23, effective_date="260912")
    result = diff_ach_files(left, right)
    assert result["equal"] is False
    assert result["differences"]


def test_diff_masks_sensitive_fields_and_requires_both_inputs() -> None:
    left = generate_ach_file(seed=22, effective_date="260912")
    result = diff_ach_files_tool(left_content=left)
    assert result["error"]["code"] == "INPUT_MISSING"
    result = diff_ach_files_tool(left_content=left, right_content=left)
    assert result["equal"] is True
    assert result["masked"] is True
