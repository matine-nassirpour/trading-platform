from dataclasses import dataclass
from decimal import Decimal

from quantum.domain.shared_kernel.foundation.errors.invariants import InvariantViolation
from quantum.domain.shared_kernel.modeling.monetary.contextual_monetary_amount import (
    ContextualMonetaryAmount,
)


@dataclass(frozen=True, slots=True)
class RiskAmount(ContextualMonetaryAmount):
    """
    Monetary risk amount allocated to a single sizing decision.
    """

    @classmethod
    def nominal_type(cls) -> str:
        return "risk_amount"

    def _validate_numeric_semantics(self) -> None:
        super()._validate_numeric_semantics()

        if self.value <= Decimal("0"):
            raise InvariantViolation("RiskAmount must be strictly positive")
