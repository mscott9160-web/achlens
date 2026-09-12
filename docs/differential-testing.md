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

The harness generates cases for:

- a valid balanced file
- an invalid routing check digit
- a bad batch control count
- a bad file hash
- invalid padding/block structure

When the environment variable is unset, the harness exits successfully with a
skip message. This keeps ordinary local and pull-request tests independent of
Docker, external services, and network access.

Before connecting a moov-io/ach container or other validator, document its
version, command contract, and disagreement triage results. Do not send real
ACH data to an external validator.
