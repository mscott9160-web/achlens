"""Initial TEL support coverage."""

from achlens.core import generate_ach_file, parse, validate


def test_tel_uses_web_tel_entry_layout_without_addenda() -> None:
    content = generate_ach_file(
        sec_code="TEL",
        entries_per_batch=2,
        include_addenda=True,
        seed=14,
        effective_date="260912",
    )
    parsed = parse(content)
    entry = parsed.batches[0].entries[0]
    assert entry.detail.layout == "entry_detail_web"
    assert not entry.addenda
    assert entry.detail.fields["payment_type_code"].raw.strip() == "S"
    assert validate(content).valid


def test_tel_is_recognized_with_out_of_v1_warning() -> None:
    content = generate_ach_file(sec_code="TEL", seed=14, effective_date="260912")
    report = validate(content)
    assert report.counts_by_rule.get("BH004", 0) == 1
    assert report.valid
