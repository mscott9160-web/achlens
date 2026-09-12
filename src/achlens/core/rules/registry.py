"""Rule catalog loading and implementation parity checks."""

from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass
from importlib.resources import files
from pathlib import Path
from typing import Any, cast

import yaml

RuleFunction = Callable[[Any], Iterable[Any]]
_REQUIRED_FIELDS = (
    "id",
    "category",
    "severity",
    "title",
    "description",
    "fix_hint",
    "applies_to",
    "source",
    "status",
)
_VALID_SEVERITIES = {"error", "warning", "info"}
_VALID_STATUSES = {"VERIFIED", "UNVERIFIED"}


@dataclass(frozen=True)
class RuleSpec:
    """Metadata describing one validation rule."""

    id: str
    category: str
    severity: str
    title: str
    description: str
    fix_hint: str
    applies_to: tuple[str, ...]
    source: str
    status: str


class RuleRegistry:
    """Catalog-backed registry of rule implementations."""

    def __init__(self, specs: Mapping[str, RuleSpec] | Iterable[RuleSpec] = ()) -> None:
        values = tuple(specs.values()) if isinstance(specs, Mapping) else tuple(specs)
        self._specs: dict[str, RuleSpec] = {}
        self._implementations: dict[str, RuleFunction] = {}
        for spec in values:
            self.add_spec(spec)

    @property
    def specs(self) -> Mapping[str, RuleSpec]:
        return self._specs

    @property
    def implementations(self) -> Mapping[str, RuleFunction]:
        return self._implementations

    def add_spec(self, spec: RuleSpec) -> None:
        if spec.id in self._specs:
            raise ValueError(f"duplicate rule ID: {spec.id}")
        self._specs[spec.id] = spec

    def register(self, rule_id: str, function: RuleFunction) -> RuleFunction:
        if rule_id not in self._specs:
            raise ValueError(f"rule implementation {rule_id!r} is absent from catalog")
        if rule_id in self._implementations:
            raise ValueError(f"duplicate rule implementation: {rule_id}")
        self._implementations[rule_id] = function
        return function

    def parity_check(self) -> None:
        catalog_ids = set(self._specs)
        implementation_ids = set(self._implementations)
        missing = sorted(catalog_ids - implementation_ids)
        extra = sorted(implementation_ids - catalog_ids)
        if missing or extra:
            details: list[str] = []
            if missing:
                details.append(f"missing implementations: {', '.join(missing)}")
            if extra:
                details.append(
                    f"implementations absent from catalog: {', '.join(extra)}"
                )
            raise ValueError("rule registry parity check failed; " + "; ".join(details))

    def decorator(self, rule_id: str) -> Callable[[RuleFunction], RuleFunction]:
        def register(function: RuleFunction) -> RuleFunction:
            return self.register(rule_id, function)

        return register


def _required(row: Mapping[str, Any], field: str, index: int) -> Any:
    if field not in row:
        raise ValueError(f"catalog row {index} is missing required key {field!r}")
    return row[field]


def _parse_spec(row: object, index: int) -> RuleSpec:
    if not isinstance(row, Mapping):
        raise ValueError(f"catalog row {index} must be a mapping")
    values = cast(Mapping[str, Any], row)
    raw = {field: _required(values, field, index) for field in _REQUIRED_FIELDS}
    scalar_fields = set(_REQUIRED_FIELDS) - {"applies_to"}
    if not all(isinstance(raw[field], str) and raw[field] for field in scalar_fields):
        raise ValueError(f"catalog row {index} has empty or non-string metadata")
    applies_to = raw["applies_to"]
    if not isinstance(applies_to, list) or not all(
        isinstance(item, str) for item in applies_to
    ):
        raise ValueError(f"catalog row {index} applies_to must be a list of strings")
    if raw["severity"] not in _VALID_SEVERITIES:
        raise ValueError(
            f"catalog row {index} has invalid severity {raw['severity']!r}"
        )
    if raw["status"] not in _VALID_STATUSES:
        raise ValueError(f"catalog row {index} has invalid status {raw['status']!r}")
    return RuleSpec(**{**raw, "applies_to": tuple(applies_to)})


def load_rule_registry(path: str | Path | None = None) -> RuleRegistry:
    """Load and validate the packaged rule catalog."""
    source = (
        Path(path)
        if path is not None
        else Path(files("achlens.core.data").joinpath("rules.yaml"))
    )
    with source.open(encoding="utf-8") as stream:
        raw = yaml.safe_load(stream)
    if not isinstance(raw, list):
        raise ValueError("rule catalog YAML must contain a list of rows")
    registry = RuleRegistry()
    for index, row in enumerate(raw, start=1):
        if isinstance(row, Mapping) and "id" not in row and row.get("template") is True:
            continue
        registry.add_spec(_parse_spec(row, index))
    return registry


def default_rule_registry() -> RuleRegistry:
    """Return the packaged catalog, ready for rule registration."""
    return load_rule_registry()


__all__ = [
    "RuleFunction",
    "RuleRegistry",
    "RuleSpec",
    "default_rule_registry",
    "load_rule_registry",
]
