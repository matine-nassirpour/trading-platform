from abc import ABC
from dataclasses import dataclass
from decimal import Decimal

from quantum.domain.shared_kernel.foundation.errors.invariants import InvariantViolation
from quantum.domain.shared_kernel.modeling.monetary.contextual_monetary_amount import (
    ContextualMonetaryAmount,
)


@dataclass(frozen=True, slots=True)
class RiskMonetaryAmount(ContextualMonetaryAmount, ABC):
    """
    Abstract root for all monetary quantities owned by risk_governance.
    """

    def _validate_numeric_semantics(self) -> None:
        super()._validate_numeric_semantics()


@dataclass(frozen=True, slots=True)
class NonNegativeRiskMeasurement(RiskMonetaryAmount, ABC):
    """
    Risk measurement constrained to value >= 0.

    Examples:
    - Drawdown
    - DailyLoss
    - Exposure
    - Notional
    """

    def _validate_numeric_semantics(self) -> None:
        super()._validate_numeric_semantics()

        if self.value < Decimal("0"):
            raise InvariantViolation(f"{self.__class__.__name__} must be non-negative")


@dataclass(frozen=True, slots=True)
class PositiveRiskLimit(RiskMonetaryAmount, ABC):
    """
    Risk governance limit constrained to value > 0.

    Examples:
    - DrawdownLimit
    - DailyLossLimit
    - ExposureLimit
    - NotionalLimit
    """

    def _validate_numeric_semantics(self) -> None:
        super()._validate_numeric_semantics()

        if self.value <= Decimal("0"):
            raise InvariantViolation(
                f"{self.__class__.__name__} must be strictly positive"
            )
