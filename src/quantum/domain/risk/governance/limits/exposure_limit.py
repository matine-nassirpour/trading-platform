from dataclasses import dataclass
from decimal import Decimal

from quantum.domain.shared_kernel.errors.invariants import InvariantViolation
from quantum.domain.shared_kernel.money.contextual_monetary_amount import (
    ContextualMonetaryAmount,
)


@dataclass(frozen=True, slots=True)
class ExposureLimit(ContextualMonetaryAmount):
    """
    Maximum allowed risk exposure.

    Exposure represents the *effective economic risk* carried by the system,
    after taking into account leverage, direction, and risk aggregation.

    This limit defines a HARD RISK BOUNDARY used by the risk governance layer
    to determine whether trading activity must be restricted or stopped.
    """

    @classmethod
    def nominal_type(cls) -> str:
        return "exposure_limit"

    def _validate_numeric_semantics(self) -> None:
        super()._validate_numeric_semantics()

        if self.value <= Decimal("0"):
            raise InvariantViolation("ExposureLimit must be strictly positive")
