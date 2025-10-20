"""
Quantum Core Configuration Validators — Rule Registry
──────────────────────────────────────────────────────
Central registry tracking all available validation rules
and exposing introspection and retrieval APIs.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from quantum.core.config.validators import common
from quantum.core.config.validators.base import (
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

    # -------------------------------------------------------------------------
    # Registration
    # -------------------------------------------------------------------------
    @classmethod
    def register(cls, rule: ValidationRule) -> None:
        if rule.rule_id in cls._registry:
            raise ValueError(f"Duplicate validator id: {rule.rule_id}")
        cls._registry[rule.rule_id] = rule

    @classmethod
    def register_defaults(cls) -> None:
        """Register all default Quantum validators."""
        cls.register(common.EnvironmentValidator())
        cls.register(common.LogLevelValidator())
        cls.register(common.TimezoneValidator())
        cls.register(common.OtlpProtocolValidator())
        cls.register(common.CompressionValidator())

    # -------------------------------------------------------------------------
    # Lookup
    # -------------------------------------------------------------------------
    @classmethod
    def get(cls, rule_id: str) -> ValidationRule:
        try:
            return cls._registry[rule_id]
        except KeyError:
            raise KeyError(f"Validator not found: {rule_id}")

    @classmethod
    def all(cls) -> Mapping[str, ValidationRule]:
        return dict(cls._registry)

    # -------------------------------------------------------------------------
    # Execution helpers
    # -------------------------------------------------------------------------
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
