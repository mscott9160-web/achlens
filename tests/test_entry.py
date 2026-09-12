"""Focused CORE-11 entry-detail rule tests."""

from achlens.core.model import AchFile, Batch, Entry, FieldValue, Record
from achlens.core.rules.entry import entry_rule_registry, validate_entries
from achlens.core.rules.structural import ValidationContext


def _record(layout: str, line: int, values: dict[str, str]) -> Record:
    fields = {}
    starts = {
        "transaction_code": 2,
        "receiving_dfi_identification": 4,
        "check_digit": 12,
        "dfi_account_number": 13,
        "amount": 30,
        "individual_name": 55,
        "receiving_company_name": 55,
        "payment_type_code": 77,
        "addenda_record_indicator": 79,
        "trace_number": 80,
    }
    for name, value in values.items():
        start = starts.get(name, 1)
        fields[name] = FieldValue(name, start, start + len(value) - 1, value, value)
    return Record(line, "6", layout, "6" + " " * 93, fields)


def _context(
    sec: str = "PPD", entries: list[Record] | None = None, odfi: str = "12345678"
) -> ValidationContext:
    header = Record(
        2,
        "5",
        "batch_header",
        "5" + " " * 93,
        {
            "service_class_code": FieldValue("service_class_code", 2, 4, "220", 220),
            "standard_entry_class_code": FieldValue(
                "standard_entry_class_code", 51, 53, sec, sec
            ),
            "odfi_identification": FieldValue(
                "odfi_identification", 80, 87, odfi, odfi
            ),
        },
    )
    default = _record(
        {
            "PPD": "entry_detail_ppd",
            "CCD": "entry_detail_ccd",
            "WEB": "entry_detail_web",
        }[sec],
        3,
        {
            "transaction_code": "22",
            "receiving_dfi_identification": "12345678",
            "check_digit": "0",
            "dfi_account_number": "ACCOUNT",
            "amount": "0000000001",
            "individual_name": "PERSON",
            "receiving_company_name": "COMPANY",
            "payment_type_code": "S",
            "addenda_record_indicator": "0",
            "trace_number": odfi + "0000001",
        },
    )
    batch = Batch(
        header=header, entries=[Entry(record) for record in (entries or [default])]
    )
    return ValidationContext("", None, AchFile(batches=[batch]))  # type: ignore[arg-type]


def _ids(context: ValidationContext) -> set[str]:
    return {finding.rule_id for finding in validate_entries(context)}


def test_registry_has_exactly_all_entry_rules() -> None:
    assert set(entry_rule_registry.specs) == {f"ED{i:03d}" for i in range(1, 17)}
    assert set(entry_rule_registry.implementations) == set(entry_rule_registry.specs)


def test_each_ed_rule_has_a_triggering_fixture() -> None:
    base = _context()
    record = base.ach_file.batches[0].entries[0].detail
    cases = {
        "ED001": {"transaction_code": "99"},
        "ED002": {"transaction_code": "27"},
        "ED003": {"receiving_dfi_identification": "BAD"},
        "ED004": {"check_digit": "9"},
        "ED005": {"dfi_account_number": "                 "},
        "ED006": {"amount": "BAD"},
        "ED007": {"transaction_code": "23", "amount": "0000000001"},
        "ED008": {"amount": "0000000000"},
        "ED009": {"individual_name": "                      "},
        "ED010": {"addenda_record_indicator": "2"},
        "ED011": {"trace_number": "123"},
        "ED012": {"trace_number": "123456780000000"},
        "ED013": {"trace_number": "123456780000001"},
        "ED014": {"trace_number": "999999990000001"},
        "ED015": {"payment_type_code": "X"},
        "ED016": {"transaction_code": "24"},
    }
    second = _record(
        record.layout, 4, {name: field.raw for name, field in record.fields.items()}
    )
    for rule_id, changes in cases.items():
        values = {name: field.raw for name, field in record.fields.items()}
        values.update(changes)
        entries = [record]
        if rule_id in {"ED012", "ED013"}:
            entries = [record, second]
            if rule_id == "ED012":
                values["trace_number"] = "123456780000002"
                entries[0] = _record(record.layout, 3, values)
            else:
                entries[1] = _record(record.layout, 4, values)
        else:
            entries[0] = _record(record.layout, 3, values)
        sec = "WEB" if rule_id == "ED015" else "PPD"
        if rule_id == "ED015":
            entries[0] = _record("entry_detail_web", 3, values)
        assert rule_id in _ids(_context(sec, entries=entries)), rule_id


def test_valid_ppd_ccd_web_entries_and_severity_differences() -> None:
    for sec in ("PPD", "CCD", "WEB"):
        context = _context(sec)
        assert not _ids(context)
    warning_ids = {
        finding.rule_id
        for finding in validate_entries(_context())
        if finding.severity == "warning"
    }
    assert warning_ids == set()


def test_rdfi_requires_exactly_eight_numeric_digits() -> None:
    for rdfi in ("1234567", "123456789"):
        findings = validate_entries(
            _context(
                entries=[
                    _record(
                        "entry_detail_ppd",
                        3,
                        {
                            "transaction_code": "22",
                            "receiving_dfi_identification": rdfi,
                            "check_digit": "0",
                            "dfi_account_number": "ACCOUNT",
                            "amount": "0000000001",
                            "individual_name": "PERSON",
                            "addenda_record_indicator": "0",
                            "trace_number": "123456780000001",
                        },
                    )
                ]
            )
        )
        assert {finding.rule_id for finding in findings} == {"ED003"}


def test_amount_requires_exactly_ten_numeric_digits() -> None:
    for amount in ("000000001", "00000000001"):
        findings = validate_entries(
            _context(
                entries=[
                    _record(
                        "entry_detail_ppd",
                        3,
                        {
                            "transaction_code": "22",
                            "receiving_dfi_identification": "12345678",
                            "check_digit": "0",
                            "dfi_account_number": "ACCOUNT",
                            "amount": amount,
                            "individual_name": "PERSON",
                            "addenda_record_indicator": "0",
                            "trace_number": "123456780000001",
                        },
                    )
                ]
            )
        )
        assert {finding.rule_id for finding in findings} == {"ED006"}


def test_check_digit_reports_missing_and_malformed_values() -> None:
    for check_digit, message in (("", "missing"), ("AB", "one digit")):
        findings = validate_entries(
            _context(
                entries=[
                    _record(
                        "entry_detail_ppd",
                        3,
                        {
                            "transaction_code": "22",
                            "receiving_dfi_identification": "12345678",
                            "check_digit": check_digit,
                            "dfi_account_number": "ACCOUNT",
                            "amount": "0000000001",
                            "individual_name": "PERSON",
                            "addenda_record_indicator": "0",
                            "trace_number": "123456780000001",
                        },
                    )
                ]
            )
        )
        finding = next(finding for finding in findings if finding.rule_id == "ED004")
        assert message in finding.message


def test_invalid_web_payment_type_is_explicit_warning() -> None:
    findings = validate_entries(
        _context(
            "WEB",
            entries=[
                _record(
                    "entry_detail_web",
                    3,
                    {
                        "transaction_code": "22",
                        "receiving_dfi_identification": "12345678",
                        "check_digit": "0",
                        "dfi_account_number": "ACCOUNT",
                        "amount": "0000000001",
                        "individual_name": "PERSON",
                        "payment_type_code": "X",
                        "addenda_record_indicator": "0",
                        "trace_number": "123456780000001",
                    },
                )
            ],
        )
    )
    finding = next(finding for finding in findings if finding.rule_id == "ED015")
    assert finding.severity == "warning"


def test_leading_account_space_and_live_zero_are_warnings() -> None:
    context = _context(
        entries=[
            _record(
                "entry_detail_ppd",
                3,
                {
                    "transaction_code": "22",
                    "receiving_dfi_identification": "12345678",
                    "check_digit": "0",
                    "dfi_account_number": " ACCOUNT",
                    "amount": "0000000000",
                    "individual_name": "PERSON",
                    "addenda_record_indicator": "0",
                    "trace_number": "123456780000001",
                },
            )
        ]
    )
    findings = validate_entries(context)
    assert {finding.rule_id for finding in findings} == {"ED005", "ED008"}
    assert all(finding.severity == "warning" for finding in findings)
