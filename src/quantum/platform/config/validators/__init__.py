"""
Quantum Core Configuration Validators — Public API
───────────────────────────────────────────────────
Provides the unified entrypoints for all validation
operations within the Quantum configuration system.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from quantum.platform.config.validators.base import ValidationContext, ValidationResult
from quantum.platform.config.validators.registry import ValidatorRegistry


def validate_field(
    rule_id: str, value: Any, *, field: str | None = None, model: str | None = None
) -> Any:
    """
    Validate a single field using a registered rule and return the validated value.
    Raises ValueError if validation fails.
    """
    context = ValidationContext(field_name=field, model_name=model)
    result: ValidationResult = ValidatorRegistry.validate(
        rule_id, value, context=context
    )
    return result.raise_if_failed()


def validate_model(model_name: str, values: Mapping[str, Any]) -> Mapping[str, Any]:
    """
    Apply all known validators whose field names match rule identifiers.
    Used for whole-model validation if needed.
    """
    validated = dict(values)
    for rule_id, rule in ValidatorRegistry.all().items():
        field = rule_id.split(".")[-1]
        if field in values:
            ctx = ValidationContext(field_name=field, model_name=model_name)
            res = rule(values[field], context=ctx)
            validated[field] = res.raise_if_failed()
    return validated


def get_registered_rules() -> Mapping[str, str]:
    """Return a mapping of rule_id -> description for documentation."""
    return {rid: r.description for rid, r in ValidatorRegistry.all().items()}
