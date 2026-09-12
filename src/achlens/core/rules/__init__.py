"""Rule catalog and registration APIs."""

from .registry import (
    RuleFunction,
    RuleRegistry,
    RuleSpec,
    default_rule_registry,
    load_rule_registry,
)
from .structural import Finding, ValidationContext, structural_rule_registry, validate_structure
from .headers import header_rule_registry, validate_headers
from .entry import entry_rule_registry, validate_entries

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
]
