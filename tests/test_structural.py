from achlens.core.builder import build_record
from achlens.core.layouts import default_layouts
from achlens.core.rules.structural import ValidationContext, validate_structure


def codes(text: str) -> set[str]:
    return {finding.rule_id for finding in validate_structure(text)}


def test_valid_length_and_printable_record_built_from_layout():
    layout = default_layouts()["file_header"]
    fields = {}
    for field in layout.fields:
        if field.required:
            fields[field.name] = "0" if field.type == "N" else "A"
    record = build_record(layout, **fields)
    assert len(record) == 94
    assert "S001" not in codes(record)
    assert "S002" not in codes(record)


def test_each_structural_rule_has_a_trigger():
    cases = {
        "S001": "1" + " " * 92,
        "S002": "1" + "\x01" + " " * 92,
        "S003": "X" + " " * 93,
        "S004": "5" + " " * 93,
        "S005": "1" + " " * 93 + "\n" + "1" + " " * 93,
        "S006": "1" + " " * 93 + "\n" + "8" + " " * 93,
        "S007": "1" + " " * 93 + "\n" + "5" + " " * 93 + "\n" + "8" + " " * 93,
        "S008": "1" + " " * 93,
        "S009": "1" + " " * 93 + "\n" + "5" + " " * 93 + "\n" + "8" + " " * 93 + "\n" + "9" + " " * 93 + "\n" + "5" + " " * 93,
        "S010": "1" + " " * 93 + "\n" + "5" + " " * 93 + "\n" + "8" + " " * 93 + "\n" + "9" + " " * 93 + "\n" + "9" + " " * 93,
        "S011": "1" + " " * 93,
        "S012": "1" + " " * 93 + "\n" + "5" + " " * 93 + "\n" + "8" + " " * 93 + "\n" + "9" + " " * 93 + "\n" + "9" * 94 + "\n" + "9" * 94,
        "S013": "1" + " " * 93 + "\r\n" + "5" + " " * 93 + "\n",
        "S014": "",
    }
    for rule_id, text in cases.items():
        assert rule_id in codes(text), rule_id


def test_valid_negative_for_empty_structure_is_explicit():
    context = ValidationContext.from_text("1" + " " * 93)
    findings = validate_structure(context)
    assert all(finding.rule_id in {"S007", "S008", "S011", "S012"} for finding in findings)


def test_empty_file_reports_missing_header():
    assert "S004" in codes("")


def test_all_nines_before_control_do_not_become_padding():
    text = "\n".join(["1" + " " * 93, "5" + " " * 93, "9" * 94, "8" + " " * 93])
    assert "S006" in codes(text)
    assert "S008" in codes(text)


def test_post_control_records_are_checked_by_record_kind():
    text = "\n".join([
        "1" + " " * 93,
        "5" + " " * 93,
        "8" + " " * 93,
        "9" + " " * 93,
        "9" + " " * 93,
        "5" + " " * 93,
    ])
    findings = validate_structure(text)
    assert sum(f.rule_id == "S009" for f in findings) == 2
    assert sum(f.rule_id == "S010" for f in findings) == 1


def test_padding_count_uses_records_through_control_boundary():
    valid = "\n".join(["1" + " " * 93, "5" + " " * 93, "8" + " " * 93, "9" + " " * 93] + ["9" * 94] * 6)
    insufficient = "\n".join(valid.splitlines()[:-1])
    unnecessary = valid + "\n" + "9" * 94
    assert "S012" not in codes(valid)
    assert "S012" in codes(insufficient)
    assert "S012" in codes(unnecessary)
