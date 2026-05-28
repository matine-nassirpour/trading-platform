from abc import ABC
from dataclasses import dataclass
from decimal import Decimal

from quantum.domain.shared_kernel.foundation.errors.invariants import InvariantViolation
from quantum.domain.shared_kernel.modeling.value_objects.numeric_value_object import (
    NumericValueObject,
)


@dataclass(frozen=True, slots=True)
class PositiveRiskScalarLimit(NumericValueObject, ABC):
    """
    Abstract root for strictly positive scalar limits.

    Example:
    - LeverageLimit
    """

    def _validate_numeric_semantics(self) -> None:
        super()._validate_numeric_semantics()

        if self.value <= Decimal("0"):
            raise InvariantViolation(
                f"{self.__class__.__name__} must be strictly positive"
            )
