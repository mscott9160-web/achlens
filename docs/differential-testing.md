# Differential Testing

The optional differential harness compares achlens with an external ACH
validator using synthetic files only.

The external command must accept one file path and print JSON with a boolean
`valid` field. Configure the command prefix through
`ACHLENS_DIFFERENTIAL_COMMAND`:

```text
$env:ACHLENS_DIFFERENTIAL_COMMAND = "external-validator --file"
python scripts/differential_validation.py
```

The harness generates a deterministic 100-case corpus: 20 seeded variants of
each of these mutations:

- a valid balanced file
- an invalid routing check digit
- a bad batch control count
- a bad file hash
- invalid padding/block structure

To write a structured disagreement report, pass an artifact path:

```text
python scripts/differential_validation.py --artifact differential-results/disagreements.json
```

The report contains `case_count` and a `disagreements` array. Each disagreement
records `rule`, `mutation`, `case`, `triage_status`, and `detail`; new findings
start as `untriaged`.

When the environment variable is unset, the harness exits successfully with a
skip message. This keeps ordinary local and pull-request tests independent of
Docker, external services, and network access.

Before connecting a moov-io/ach container or other validator, document its
version, command contract, and disagreement triage results. Do not send real
ACH data to an external validator.

## Optional workflow and release treatment

`.github/workflows/differential-validation.yml` is separate from normal CI and
release workflows. It runs only from `workflow_dispatch` or its weekly
schedule, and uploads the structured report even when validation fails. It
exits successfully with a clear skipped artifact when the
`ACHLENS_DIFFERENTIAL_COMMAND` secret is absent. Differential validation is
evidence for release review, not a required PR gate or release prerequisite.
