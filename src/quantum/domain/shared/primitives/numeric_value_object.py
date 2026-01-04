from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from decimal import Decimal

from quantum.domain.shared.errors.invariants import InvariantViolation
from quantum.domain.shared.primitives.value_object import ValueObject


@dataclass(frozen=True)
class NumericValueObject(ValueObject, ABC):
    """
    Canonical base class for all numeric Value Objects.

    Design guarantees:
    - Immutable
    - Deterministic validation
    - Explicit numeric invariants
    - No NaN / Infinity
    - No floating-point arithmetic

    This abstraction is intentionally generic and unit-agnostic.
    """

    value: Decimal

    def _validate(self) -> None:
        self._validate_type()
        self._validate_finite()
        self._validate_semantics()

    # --- Mandatory hooks ------------------------------------------------------

    @abstractmethod
    def _validate_type(self) -> None:
        """
        Enforces the concrete numeric type (usually Decimal).
        """
        raise NotImplementedError

    @abstractmethod
    def _validate_semantics(self) -> None:
        """
        Enforces domain-specific numeric invariants
        (e.g. > 0, >= 0, bounded, etc.).
        """
        raise NotImplementedError

    # --- Shared numeric invariants --------------------------------------------

    def _validate_finite(self) -> None:
        """
        Enforces that the numeric value is finite and defined.

        This is a hard invariant for all financial / risk quantities.
        """
        if not isinstance(self.value, Decimal):
            # Defensive: type check is duplicated intentionally
            raise InvariantViolation(
                f"{self.__class__.__name__} value must be a Decimal"
            )

        if self.value.is_nan():
            raise InvariantViolation(f"{self.__class__.__name__} must not be NaN")

        if self.value.is_infinite():
            raise InvariantViolation(f"{self.__class__.__name__} must be finite")
