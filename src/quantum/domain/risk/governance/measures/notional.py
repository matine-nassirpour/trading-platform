from dataclasses import dataclass
from decimal import Decimal

from quantum.domain.shared_kernel.foundation.errors.invariants import InvariantViolation
from quantum.domain.shared_kernel.monetary.contextual_monetary_amount import (
    ContextualMonetaryAmount,
)


@dataclass(frozen=True, slots=True)
class Notional(ContextualMonetaryAmount):
    """
    Contractual notional amount.

    Represents the *gross contractual size* of a position or exposure.
    It is a structural quantity used for:

    - trade sizing
    - margin and fee calculations
    - regulatory and reporting purposes
    - exposure decomposition
    """

    @classmethod
    def nominal_type(cls) -> str:
        return "notional"

    def _validate_numeric_semantics(self) -> None:
        super()._validate_numeric_semantics()

        if self.value < Decimal("0"):
            raise InvariantViolation("Notional must be non-negative")
