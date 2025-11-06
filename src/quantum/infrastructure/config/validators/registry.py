"""
Quantum Core Configuration Validators — Rule Registry
─────────────────────────────────────────────────────
Central registry tracking all available validation rules
and exposing introspection and retrieval APIs.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from quantum.infrastructure.config.validators import rules
from quantum.infrastructure.config.validators.base import (
    ValidationContext,
    ValidationResult,
    ValidationRule,
)


class ValidatorRegistry:
    """
    Central registry of all validation rules in the system.

    - Provides declarative access by rule_id
    - Supports registration of custom rules
    - Offers safe execution wrappers (with result capture)
    """

    _registry: dict[str, ValidationRule] = {}

    # --------------------------------------------------------------------------
    # Lifecycle Management
    # --------------------------------------------------------------------------
    @classmethod
    def clear_registry(cls) -> None:
        """
        Completely clear the validator registry.

        Used for test isolation or controlled lifecycle resets.
        """
        cls._registry.clear()

    # --------------------------------------------------------------------------
    # Registration
    # --------------------------------------------------------------------------
    @classmethod
    def register(cls, rule: ValidationRule) -> None:
        if rule.rule_id in cls._registry:
            raise ValueError(f"Duplicate validator id: {rule.rule_id}")
        cls._registry[rule.rule_id] = rule

    @classmethod
    def register_defaults(cls) -> None:
        """Register all default Quantum validators."""
        defaults = {
            "platform.runtime.environment": rules.EnvironmentValidator,
            "platform.logging.log_level": rules.LogLevelValidator,
            "platform.logging.timezone": rules.TimezoneValidator,
            "platform.tracing.otlp_protocol": rules.OtlpProtocolValidator,
            "platform.tracing.compression": rules.CompressionValidator,
        }

        for rid, factory in defaults.items():
            if rid not in cls._registry:
                cls.register(factory())

    # --------------------------------------------------------------------------
    # Lookup
    # --------------------------------------------------------------------------
    @classmethod
    def get(cls, rule_id: str) -> ValidationRule:
        """Retrieve a registered validation rule by id."""
        try:
            return cls._registry[rule_id]
        except KeyError as e:
            raise KeyError(f"Validator not found: {rule_id}") from e

    @classmethod
    def all(cls) -> Mapping[str, ValidationRule]:
        """Return a shallow copy of the registry for inspection."""
        return dict(cls._registry)

    # --------------------------------------------------------------------------
    # Execution helpers
    # --------------------------------------------------------------------------
    @classmethod
    def validate(
        cls,
        rule_id: str,
        value: Any,
        *,
        context: ValidationContext | None = None,
    ) -> ValidationResult:
        """Execute a registered validation rule."""
        rule = cls.get(rule_id)
        return rule(value, context=context)


# Initialize default rules at import time
ValidatorRegistry.register_defaults()
