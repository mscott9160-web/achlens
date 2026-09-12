"""Tests for the CORE-08 rule catalog and registry."""

from pathlib import Path

import pytest
import yaml

from achlens.core.rules.registry import RuleRegistry, RuleSpec, load_rule_registry


EXPECTED_IDS = {
    *(f"S{i:03d}" for i in range(1, 15)),
    *(f"FH{i:03d}" for i in range(1, 11)),
    *(f"BH{i:03d}" for i in range(1, 12)),
    *(f"ED{i:03d}" for i in range(1, 17)),
    *(f"AD{i:03d}" for i in range(1, 9)),
    *(f"BC{i:03d}" for i in range(1, 10)),
    *(f"FC{i:03d}" for i in range(1, 8)),
}


def _spec(rule_id: str = "S001") -> RuleSpec:
    return RuleSpec(rule_id, "S", "error", "title", "description", "fix", ("all",), "source", "UNVERIFIED")


def _stub(_context):
    return ()


def test_catalog_contains_declared_ids_and_representative_metadata() -> None:
    registry = load_rule_registry()

    assert len(registry.specs) == 75
    assert set(registry.specs) == EXPECTED_IDS
    assert registry.specs["S001"].fix_hint.startswith("Editors may strip")
    assert registry.specs["S013"].severity == "warning"
    assert registry.specs["FH004"].status == "UNVERIFIED"
    assert registry.specs["FC001"].source == "achlens convention"


def test_parity_reports_missing_implementation() -> None:
    registry = RuleRegistry([_spec()])

    with pytest.raises(ValueError, match="missing implementations: S001"):
        registry.parity_check()


def test_parity_reports_extra_implementation() -> None:
    registry = RuleRegistry([_spec()])
    registry._implementations["NOPE"] = _stub

    with pytest.raises(ValueError, match="implementations absent from catalog: NOPE"):
        registry.parity_check()


def test_duplicate_catalog_ids_are_rejected() -> None:
    with pytest.raises(ValueError, match="duplicate rule ID: S001"):
        RuleRegistry([_spec(), _spec()])


def test_duplicate_implementation_ids_are_rejected() -> None:
    registry = RuleRegistry([_spec()])
    registry.register("S001", _stub)

    with pytest.raises(ValueError, match="duplicate rule implementation: S001"):
        registry.register("S001", _stub)


def test_malformed_catalog_row_is_rejected(tmp_path: Path) -> None:
    path = tmp_path / "malformed.yaml"
    path.write_text(yaml.safe_dump([{"id": "S001", "category": "S"}]), encoding="utf-8")

    with pytest.raises(ValueError, match="missing required key 'severity'"):
        load_rule_registry(path)


def test_non_template_row_without_id_is_rejected(tmp_path: Path) -> None:
    path = tmp_path / "missing-id.yaml"
    path.write_text(
        yaml.safe_dump(
            [
                {
                    "category": "S",
                    "severity": "error",
                    "title": "Missing ID",
                    "description": "An ordinary rule without an ID.",
                    "fix_hint": "Add an ID.",
                    "applies_to": ["all"],
                    "source": "test",
                    "status": "UNVERIFIED",
                }
            ]
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="missing required key 'id'"):
        load_rule_registry(path)
