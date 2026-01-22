from dataclasses import dataclass
from decimal import Decimal

from quantum.domain.shared_kernel.errors.invariants import InvariantViolation
from quantum.domain.shared_kernel.money.contextual_monetary_amount import (
    ContextualMonetaryAmount,
)


@dataclass(frozen=True, slots=True)
class Margin(ContextualMonetaryAmount):
    """
    Represents margin usage and availability.
    """

    used: ContextualMonetaryAmount
    available: ContextualMonetaryAmount

    def _validate(self) -> None:
        if self.used.context != self.available.context:
            raise InvariantViolation("Margin contexts must match")

        if self.used.currency != self.available.currency:
            raise InvariantViolation("Margin currencies must match")

        if self.used.value < 0 or self.available.value < 0:
            raise InvariantViolation("Margin values must be non-negative")

    @property
    def utilization_ratio(self) -> Decimal:
        total = self.used.value + self.available.value
        return 0 if total == 0 else self.used.value / total
