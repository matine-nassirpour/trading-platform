from __future__ import annotations

import abc

from collections.abc import Mapping
from dataclasses import dataclass, field
from types import MappingProxyType
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


@dataclass(frozen=True, slots=True)
class ValidationContext:
    """
    Immutable context passed to validators for additional information.

    Guarantees:
        • Fully immutable (frozen dataclass + mapping proxy)
        • Zero side effects, zero mutation
        • Suitable for safety-critical and deterministic validation
        • Safe for cross-thread usage
        • Explicit structure: model_name, field_name, extras (read-only)
    """

    model_name: str | None = None
    field_name: str | None = None
    extras: Mapping[str, Any] = field(default_factory=lambda: MappingProxyType({}))

    def __post_init__(self) -> None:
        # Convert extras to an immutable mapping proxy
        object.__setattr__(self, "extras", MappingProxyType(dict(self.extras)))

    def describe(self) -> str:
        """
        Return a canonical textual description of the context.
        Stable, deterministic and safe for logs/audit.
        """
        parts: list[str] = []

        if self.model_name:
            parts.append(f"model={self.model_name}")
        if self.field_name:
            parts.append(f"field={self.field_name}")

        return f"ValidationContext({', '.join(parts) or 'anonymous'})"


class ValidationRule(abc.ABC):
    """Abstract validator with strict/lenient structured output."""

    rule_id: str
    description: str

    def __init__(self, rule_id: str, description: str) -> None:
        self.rule_id = rule_id
        self.description = description

    @abc.abstractmethod
    def __call__(
        self, value: Any, *, context: ValidationContext | None = None
    ) -> ValidationResult:
        raise NotImplementedError

    # --------------------------------------------------------------------------
    # Helpers
    # --------------------------------------------------------------------------
    def success(self, value: Any) -> ValidationResult:
        return ValidationResult(ok=True, message=None, value=value, rule=self.rule_id)

    def failure(self, message: str, value: Any | None = None) -> ValidationResult:
        return ValidationResult(
            ok=False, message=message, value=value, rule=self.rule_id
        )
