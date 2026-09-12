"""VPR-04 field-location parity checks for the validation snapshot."""

from achlens.core import generate_ach_file, validate
from achlens.core.validation_snapshot import build_validation_snapshot


def test_validator_field_findings_resolve_in_snapshot() -> None:
    mutations = (
        ["ED004"],
        ["ED007"],
        ["ED012"],
        ["AD004"],
        ["BC002"],
        ["BC003"],
        ["BC004"],
        ["BC005"],
        ["FC001"],
        ["FC003"],
        ["FC004"],
        ["FC005"],
        ["FC006"],
    )
    for seed, inject_errors in enumerate(mutations):
        content = generate_ach_file(
            batches=2,
            entries_per_batch=2,
            include_prenotes=True,
            include_addenda=True,
            seed=seed,
            effective_date="260912",
            inject_errors=inject_errors,
        )
        snapshot = build_validation_snapshot(content)
        records = [
            record
            for batch in snapshot.batches
            for record in [batch.header, batch.control]
            if record is not None
        ]
        records.extend(
            record
            for batch in snapshot.batches
            for entry in batch.entries
            for record in [entry.detail, *entry.addenda]
        )
        if snapshot.header is not None:
            records.append(snapshot.header)
        if snapshot.file_control is not None:
            records.append(snapshot.file_control)
        by_line = {record.line.line_number: record for record in records}
        for finding in validate(content).findings:
            if finding.field is None or finding.line_number is None:
                continue
            record = by_line[finding.line_number]
            field = record.fields[finding.field]
            assert finding.position == field.start
