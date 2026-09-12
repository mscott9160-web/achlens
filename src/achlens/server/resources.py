"""Read-only MCP resources backed by packaged achlens data."""

import json

from achlens.core import default_layouts, reference_catalog
from achlens.core.rules.registry import load_rule_registry


def layouts_resource() -> str:
    layouts = {
        name: {
            "name": layout.name,
            "fields": [field.__dict__ for field in layout.fields],
        }
        for name, layout in default_layouts().items()
    }
    return json.dumps(layouts, sort_keys=True)


def rules_resource() -> str:
    rules = {
        rule_id: spec.__dict__ for rule_id, spec in load_rule_registry().specs.items()
    }
    return json.dumps(rules, sort_keys=True)


def reference_resource(kind: str) -> str:
    return json.dumps(reference_catalog(kind), sort_keys=True)


__all__ = ["layouts_resource", "reference_resource", "rules_resource"]
