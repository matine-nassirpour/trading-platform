from dataclasses import dataclass
from decimal import Decimal

from quantum.domain.shared_kernel.errors.invariants import InvariantViolation
from quantum.domain.shared_kernel.primitives.monetary_value_object import (
    MonetaryValueObject,
)
from quantum.domain.shared_kernel.value_objects.currency import Currency


@dataclass(frozen=True)
class Fee(MonetaryValueObject):
    """
    Canonical execution fee.
    Always non-negative.
    """

    value: Decimal
    currency: Currency

    def _validate_semantics(self) -> None:
        if self.value < Decimal("0"):
            raise InvariantViolation("Fee must be non-negative")
