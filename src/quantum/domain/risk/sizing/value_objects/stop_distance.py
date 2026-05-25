from dataclasses import dataclass
from decimal import Decimal

from quantum.domain.shared_kernel.foundation.errors.invariants import InvariantViolation
from quantum.domain.shared_kernel.modeling.value_objects.numeric_value_object import (
    NumericValueObject,
)


@dataclass(frozen=True, slots=True)
class StopDistance(NumericValueObject):
    """
    Absolute stop distance expressed in instrument price units.

    Example:
        EURUSD entry=1.10000, SL=1.09800
        StopDistance = Decimal("0.00200")
    """

    @classmethod
    def nominal_type(cls) -> str:
        return "stop_distance"

    def _validate_numeric_semantics(self) -> None:
        super()._validate_numeric_semantics()

        if self.value <= Decimal("0"):
            raise InvariantViolation("StopDistance must be strictly positive")
