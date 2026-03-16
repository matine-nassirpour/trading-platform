from dataclasses import dataclass
from decimal import Decimal

from quantum.domain.shared_kernel.errors.invariants import InvariantViolation
from quantum.domain.shared_kernel.money.contextual_monetary_amount import (
    ContextualMonetaryAmount,
)


@dataclass(frozen=True, slots=True)
class Exposure(ContextualMonetaryAmount):
    """
    Effective economic exposure.

    Represents the REAL economic risk carried by the system,
    after accounting for direction, leverage, and aggregation effects.

    Key properties:
    - Exposure ≠ Notional
    - Exposure reflects risk, not size
    - Exposure is always non-negative
    - Used exclusively for risk evaluation

    Examples:
        - Net position exposure
        - Delta-adjusted option exposure
        - Risk-weighted exposure
    """

    def _validate(self) -> None:
        super()._validate()

        if self.value < Decimal("0"):
            raise InvariantViolation("Exposure must be non-negative")
