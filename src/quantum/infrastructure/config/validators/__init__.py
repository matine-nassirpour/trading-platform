from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from quantum.infrastructure.config.validators.base import (
    ValidationContext,
    ValidationResult,
)
from quantum.infrastructure.config.validators.registry import ValidatorRegistry
from quantum.infrastructure.config.validators.rules import get_default_validators

# Runtime registry instance (set once at bootstrap)
_RUNTIME_REGISTRY: ValidatorRegistry | None = None


# ╭────────────────────────────────────────────────────────────────────────────╮
# │ Bootstrap API                                                              │
# ╰────────────────────────────────────────────────────────────────────────────╯
def initialize_validators(registry: ValidatorRegistry | None = None) -> None:
    """
    Initialize the runtime validator registry.
    This MUST be called exactly once during application startup.

    If no registry is provided, a default sealed registry is created.
    """
    global _RUNTIME_REGISTRY

    if _RUNTIME_REGISTRY is not None:
        # Multiple initialization forbidden — deterministic behavior enforced.
        raise RuntimeError("Validator registry has already been initialized.")

    if registry is None:
        from quantum.infrastructure.config.validators.registry import (
            ValidatorRegistryFactory,
        )

        default = get_default_validators()
        registry = ValidatorRegistryFactory.create_default(default)

    _RUNTIME_REGISTRY = registry


def _require_registry() -> ValidatorRegistry:
    if _RUNTIME_REGISTRY is None:
        raise RuntimeError(
            "Validator registry not initialized. "
            "Call initialize_validors() during application bootstrap."
        )
    return _RUNTIME_REGISTRY


# ╭────────────────────────────────────────────────────────────────────────────╮
# │ Public API                                                                 │
# ╰────────────────────────────────────────────────────────────────────────────╯
def validate_field(
    rule_id: str,
    value: Any,
    *,
    field: str | None = None,
    model: str | None = None,
) -> Any:
    registry = _require_registry()
    context = ValidationContext(field_name=field, model_name=model)
    result: ValidationResult = registry.validate(rule_id, value, context=context)
    return result.raise_if_failed()


def validate_model(model_name: str, values: Mapping[str, Any]) -> Mapping[str, Any]:
    registry = _require_registry()

    validated = dict(values)
    for rule_id, rule in registry.all().items():
        field = rule_id.split(".")[-1]

        if field in values:
            ctx = ValidationContext(field_name=field, model_name=model_name)
            res = rule(values[field], context=ctx)
            validated[field] = res.raise_if_failed()

    return validated


def get_registered_rules() -> Mapping[str, str]:
    registry = _require_registry()
    return {rid: rule.description for rid, rule in registry.all().items()}
