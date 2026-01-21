from dataclasses import dataclass
from decimal import Decimal

from quantum.domain.shared_kernel.errors.invariants import InvariantViolation
from quantum.domain.shared_kernel.money.contextual_monetary_amount import (
    ContextualMonetaryAmount,
)


@dataclass(frozen=True, slots=True)
class ExposureLimit(ContextualMonetaryAmount):
    """
    Maximum allowed market exposure.

    Examples:
    - max notional exposure
    - max position exposure
    """

    def _validate(self) -> None:
        super()._validate()

        if self.value <= Decimal("0"):
            raise InvariantViolation("ExposureLimit must be strictly positive")
