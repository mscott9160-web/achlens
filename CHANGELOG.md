# Changelog

## Unreleased

- Added the Sprint 0 repository foundation and CLI entry point.

## 0.1.7

- Updated the published README badge row. No functional changes.

## 0.1.6

- Updated package metadata, PyPI classifiers, project links, and repository
  discoverability settings. No functional changes.

## 0.1.5

- Documented the MCP tool, resource, and prompt surface and added tested
  configuration examples for VS Code/Copilot and Claude Desktop.
- Added an end-to-end stdio protocol smoke test of the built wheel.
- Updated audited runtime and development transitive dependencies.

## 0.1.2

- Enabled streaming validation by default for built-in runners, with
  `ACHLENS_DISABLE_STREAMING_VALIDATION=1` available as a rollback switch.
- Verified exact streaming/legacy parity and cross-platform benchmark evidence:
  hosted Windows, Ubuntu, and macOS runs completed in under one second, used
  53.8 MB, and produced valid reports with no errors.
- Repaired CI `PYTHONPATH` handling and hardened dependency and security checks.
