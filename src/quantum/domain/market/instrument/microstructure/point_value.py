from dataclasses import dataclass
from decimal import Decimal

from quantum.domain.shared_kernel.foundation.errors.invariants import InvariantViolation
from quantum.domain.shared_kernel.modeling.monetary.currency import Currency
from quantum.domain.shared_kernel.modeling.value_objects.numeric_value_object import (
    NumericValueObject,
)


@dataclass(frozen=True, slots=True)
class PointValue(NumericValueObject):
    """
    Monetary value of one point movement for one contract / lot.
    """

    currency: Currency

    @classmethod
    def nominal_type(cls) -> str:
        return "point_value"

    def _validate_numeric_semantics(self) -> None:
        super()._validate_numeric_semantics()

        if self.value <= Decimal("0"):
            raise InvariantViolation("PointValue must be strictly positive")

        if not isinstance(self.currency, Currency):
            raise InvariantViolation("PointValue requires a valid Currency")
