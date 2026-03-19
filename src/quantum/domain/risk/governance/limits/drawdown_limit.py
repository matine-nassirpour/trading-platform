from dataclasses import dataclass
from decimal import Decimal

from quantum.domain.shared_kernel.foundation.errors.invariants import InvariantViolation
from quantum.domain.shared_kernel.monetary.contextual_monetary_amount import (
    ContextualMonetaryAmount,
)


@dataclass(frozen=True, slots=True)
class DrawdownLimit(ContextualMonetaryAmount):
    """
    Maximum allowed drawdown.

    Properties:
    - Monetary threshold
    - Strictly positive
    - Non-algebraic (cannot be added/subtracted)
    """

    @classmethod
    def nominal_type(cls) -> str:
        return "drawdown_limit"

    def _validate_numeric_semantics(self) -> None:
        super()._validate_numeric_semantics()

        if self.value <= Decimal("0"):
            raise InvariantViolation("DrawdownLimit must be strictly positive")
