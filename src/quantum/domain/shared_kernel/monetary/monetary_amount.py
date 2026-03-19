from abc import ABC
from dataclasses import dataclass

from quantum.domain.shared_kernel.ddd.value_objects.numeric_value_object import (
    NumericValueObject,
)
from quantum.domain.shared_kernel.foundation.errors.invariants import InvariantViolation
from quantum.domain.shared_kernel.monetary.currency import Currency


@dataclass(frozen=True, slots=True)
class MonetaryAmount(NumericValueObject, ABC):
    """
    Abstract base class for all monetary domain quantities.

    HARD GUARANTEES:
    - Abstract by design: this class is NOT a complete domain concept
    - Currency-aware
    - Decimal-only
    - Immutable
    - Must be specialized into an explicit monetary meaning

    ARCHITECTURAL CONSEQUENCE:
    MonetaryAmount(value=..., currency=...) is forbidden because it does not
    specify what kind of monetary quantity it represents.
    """

    currency: Currency

    def _validate_numeric_semantics(self) -> None:
        super()._validate_numeric_semantics()

        if not isinstance(self.currency, Currency):
            raise InvariantViolation(
                f"{self.__class__.__name__} requires a valid Currency"
            )
