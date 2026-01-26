from dataclasses import dataclass

from quantum.domain.shared_kernel.errors.invariants import InvariantViolation
from quantum.domain.shared_kernel.primitives.numeric_value_object import (
    NumericValueObject,
)
from quantum.domain.shared_kernel.value_objects.currency import Currency


@dataclass(frozen=True, slots=True)
class MonetaryAmount(NumericValueObject):
    """
    Abstract base class for all monetary quantities.

    Guarantees:
    - Currency-aware
    - Decimal-only
    - Immutable
    """

    currency: Currency

    def _validate(self) -> None:
        super()._validate()

        if not isinstance(self.currency, Currency):
            raise InvariantViolation(
                f"{self.__class__.__name__} requires a valid Currency"
            )
