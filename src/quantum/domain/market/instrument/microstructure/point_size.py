from dataclasses import dataclass
from decimal import Decimal

from quantum.domain.shared_kernel.foundation.errors.invariants import InvariantViolation
from quantum.domain.shared_kernel.modeling.value_objects.numeric_value_object import (
    NumericValueObject,
)


@dataclass(frozen=True, slots=True)
class PointSize(NumericValueObject):
    """
    Canonical price point size.

    Example:
        FX 5-digit EURUSD:
            point_size = Decimal("0.00001")
        Index CFD:
            point_size = Decimal("1")
    """

    @classmethod
    def nominal_type(cls) -> str:
        return "point_size"

    def _validate_numeric_semantics(self) -> None:
        super()._validate_numeric_semantics()

        if self.value <= Decimal("0"):
            raise InvariantViolation("PointSize must be strictly positive")
