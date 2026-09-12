"""Rule catalog and registration APIs."""

from .addenda import addenda_rule_registry, validate_addenda
from .controls import control_rule_registry, validate_controls
from .entry import entry_rule_registry, validate_entries
from .headers import header_rule_registry, validate_headers
from .registry import (
    RuleFunction,
    RuleRegistry,
    RuleSpec,
    default_rule_registry,
    load_rule_registry,
)
from .structural import (
    Finding,
    ValidationContext,
    structural_rule_registry,
    validate_structure,
)

__all__ = [
    "RuleFunction",
    "RuleRegistry",
    "RuleSpec",
    "default_rule_registry",
    "load_rule_registry",
    "Finding",
    "ValidationContext",
    "structural_rule_registry",
    "validate_structure",
    "header_rule_registry",
    "validate_headers",
    "entry_rule_registry",
    "validate_entries",
    "addenda_rule_registry",
    "validate_addenda",
    "control_rule_registry",
    "validate_controls",
]
