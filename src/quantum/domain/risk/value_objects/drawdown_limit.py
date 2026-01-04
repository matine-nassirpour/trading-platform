from dataclasses import dataclass
from decimal import Decimal

from quantum.domain.shared_kernel.errors.invariants import InvariantViolation
from quantum.domain.shared_kernel.primitives.monetary_amount import MonetaryAmount
from quantum.domain.shared_kernel.primitives.value_object import ValueObject


@dataclass(frozen=True)
class DrawdownLimit(ValueObject):
    """
    Maximum allowed drawdown.

    Properties:
    - Monetary threshold
    - Strictly positive
    - Non-algebraic
    """

    value: MonetaryAmount

    def _validate(self) -> None:
        if not isinstance(self.value, MonetaryAmount):
            raise InvariantViolation("DrawdownLimit value must be a MonetaryAmount")

        if self.value.value <= Decimal("0"):
            raise InvariantViolation("DrawdownLimit must be strictly positive")
