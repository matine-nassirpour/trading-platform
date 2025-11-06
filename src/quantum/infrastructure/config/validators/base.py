"""
Quantum Core Configuration Validators — Base Contracts
──────────────────────────────────────────────────────
Defines abstract classes and base types for reusable,
composable, and introspectable validation rules.
"""

from __future__ import annotations

import abc
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class ValidationResult:
    """
    Represents the outcome of a validation operation.

    Attributes:
        ok: Whether the validation succeeded.
        message: Optional human-readable explanation.
        value: The (possibly normalized) validated value.
        rule: The name or identifier of the rule executed.
    """

    ok: bool
    message: str | None
    value: Any
    rule: str

    def raise_if_failed(self) -> Any:
        """Raise a ValueError if validation failed, else return the value."""
        if not self.ok:
            raise ValueError(self.message or f"Validation failed: {self.rule}")
        return self.value


class ValidationContext:
    """
    Immutable context passed to validators for additional information.

    Examples:
        - field_name: logical name of the field
        - model_name: Pydantic model name
        - config_env: current runtime environment
    """

    __slots__ = ("field_name", "model_name", "extras")

    def __init__(
        self,
        *,
        field_name: str | None = None,
        model_name: str | None = None,
        extras: Mapping[str, Any] | None = None,
    ) -> None:
        self.field_name = field_name
        self.model_name = model_name
        self.extras = dict(extras or {})

    def describe(self) -> str:
        parts = []
        if self.model_name:
            parts.append(f"model={self.model_name}")
        if self.field_name:
            parts.append(f"field={self.field_name}")
        return f"ValidationContext({', '.join(parts) or 'anonymous'})"


class ValidationRule(abc.ABC):
    """
    Abstract base class for all validation rules.
    """

    # Unique identifier for registry
    rule_id: str
    # Human-readable description
    description: str

    def __init__(self, rule_id: str, description: str) -> None:
        self.rule_id = rule_id
        self.description = description

    @abc.abstractmethod
    def __call__(
        self, value: Any, *, context: ValidationContext | None = None
    ) -> ValidationResult:
        """Execute validation on the given value."""
        raise NotImplementedError

    # --------------------------------------------------------------------------
    # Helpers
    # --------------------------------------------------------------------------
    def success(self, value: str) -> ValidationResult:
        return ValidationResult(ok=True, message=None, value=value, rule=self.rule_id)

    def failure(self, message: str, value: str | None = None) -> ValidationResult:
        return ValidationResult(
            ok=False, message=message, value=value, rule=self.rule_id
        )
