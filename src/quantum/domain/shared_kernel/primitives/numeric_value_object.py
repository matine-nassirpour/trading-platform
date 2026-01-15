from dataclasses import dataclass
from decimal import Decimal

from quantum.domain.shared_kernel.errors.invariants import InvariantViolation
from quantum.domain.shared_kernel.primitives.value_object import ValueObject


@dataclass(frozen=True, slots=True)
class NumericValueObject(ValueObject):
    """
    Canonical base class for all numeric Value Objects.

    Guarantees:
    - Decimal only
    - No NaN
    - No Infinity
    """

    value: Decimal

    def _validate(self) -> None:
        if not isinstance(self.value, Decimal):
            raise InvariantViolation(
                f"{self.__class__.__name__} value must be a Decimal"
            )

        if self.value.is_nan():
            raise InvariantViolation(f"{self.__class__.__name__} must not be NaN")

        if self.value.is_infinite():
            raise InvariantViolation(f"{self.__class__.__name__} must be finite")
