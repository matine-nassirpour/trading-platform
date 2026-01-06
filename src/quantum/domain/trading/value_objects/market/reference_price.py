from dataclasses import dataclass
from decimal import Decimal

from quantum.domain.shared_kernel.errors.invariants import InvariantViolation
from quantum.domain.shared_kernel.primitives.numeric_value_object import (
    NumericValueObject,
)


@dataclass(frozen=True)
class ReferencePrice(NumericValueObject):
    """
    Non-executable price used as a decision or market snapshot reference.
    """

    value: Decimal

    def _validate_semantics(self) -> None:
        if self.value < Decimal("0"):
            raise InvariantViolation("ReferencePrice must be non-negative")
