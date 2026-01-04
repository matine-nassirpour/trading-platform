from __future__ import annotations

from abc import ABC
from dataclasses import dataclass
from decimal import Decimal

from quantum.domain.shared_kernel.errors.invariants import InvariantViolation
from quantum.domain.shared_kernel.primitives.numeric_value_object import (
    NumericValueObject,
)
from quantum.domain.shared_kernel.value_objects.currency import Currency


@dataclass(frozen=True)
class MonetaryAmount(NumericValueObject, ABC):
    """
    Base class for all monetary quantities.

    Guarantees:
    - Currency-aware
    - Decimal-only
    - NO algebraic assumptions
    """

    value: Decimal
    currency: Currency

    def _validate_type(self) -> None:
        if not isinstance(self.value, Decimal):
            raise InvariantViolation("Monetary value must be a Decimal")

        if not isinstance(self.currency, Currency):
            raise InvariantViolation("Invalid currency")
