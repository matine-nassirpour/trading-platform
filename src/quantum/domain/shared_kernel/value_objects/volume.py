from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from quantum.domain.shared_kernel.errors.invariants import InvariantViolation
from quantum.domain.shared_kernel.primitives.numeric_value_object import (
    NumericValueObject,
)


@dataclass(frozen=True, slots=True)
class PositiveVolume(NumericValueObject):
    """
    Volume strictly greater than zero.
    """

    value: Decimal

    def _validate(self) -> None:
        super()._validate()

        if self.value <= Decimal("0"):
            raise InvariantViolation("PositiveVolume must be strictly > 0")


@dataclass(frozen=True, slots=True)
class NonNegativeVolume(NumericValueObject):
    """
    Volume greater than or equal to zero.

    Use cases:
    - filled volume
    - partial fills
    - closed volume
    """

    value: Decimal

    def _validate(self) -> None:
        super()._validate()

        if self.value < Decimal("0"):
            raise InvariantViolation("NonNegativeVolume must be ≥ 0")

    @classmethod
    def zero(cls) -> NonNegativeVolume:
        return cls(Decimal("0"))
