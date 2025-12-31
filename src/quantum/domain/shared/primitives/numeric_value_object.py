from __future__ import annotations

from abc import ABC
from decimal import Decimal

from quantum.domain.shared.errors.invariants import InvariantViolation
from quantum.domain.shared.primitives.value_object import ValueObject


class _NumericValueObject(ValueObject, ABC):
    """
    Internal base class for all numeric Value Objects.

    Guarantees:
    - Strict type checking
    - No NaN / Infinity
    - Deterministic failure semantics
    """

    value: object  # overridden concretely

    def _validate(self) -> None:
        self._validate_type()
        self._validate_finite()

    # --- Mandatory hooks ------------------------------------------------------

    def _validate_type(self) -> None:
        """
        Must be implemented by subclasses.
        """
        raise NotImplementedError

    # --- Shared numeric invariants --------------------------------------------

    def _validate_finite(self) -> None:
        """
        Enforces non-NaN and finite semantics for Decimal.
        """
        if isinstance(self.value, Decimal):
            if self.value.is_nan():
                raise InvariantViolation(f"{self.__class__.__name__} must not be NaN")
            if self.value.is_infinite():
                raise InvariantViolation(f"{self.__class__.__name__} must be finite")
