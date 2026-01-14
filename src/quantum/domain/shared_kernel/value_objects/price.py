from dataclasses import dataclass
from decimal import Decimal

from quantum.domain.shared_kernel.errors.invariants import InvariantViolation
from quantum.domain.shared_kernel.money.contextual_monetary_amount import (
    ContextualMonetaryAmount,
)


@dataclass(frozen=True, slots=True)
class Price(ContextualMonetaryAmount):
    """
    Strictly positive monetary quantity.
    """

    def _validate(self) -> None:
        super()._validate()

        if self.value <= Decimal("0"):
            raise InvariantViolation("Price must be strictly positive")
