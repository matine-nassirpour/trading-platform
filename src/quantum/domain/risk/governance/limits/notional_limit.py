from dataclasses import dataclass
from decimal import Decimal

from quantum.domain.shared_kernel.errors.invariants import InvariantViolation
from quantum.domain.shared_kernel.money.contextual_monetary_amount import (
    ContextualMonetaryAmount,
)


@dataclass(frozen=True, slots=True)
class NotionalLimit(ContextualMonetaryAmount):
    """
    Maximum allowed notional exposure.

    This represents a HARD constraint on the contractual size
    of positions, independent of risk-weighting or netting.

    NotionalLimit is a governance rule, not a measurement.
    """

    @classmethod
    def nominal_type(cls) -> str:
        return "notional_limit"

    def _validate_numeric_semantics(self) -> None:
        super()._validate_numeric_semantics()

        if self.value <= Decimal("0"):
            raise InvariantViolation("NotionalLimit must be strictly positive")
