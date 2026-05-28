from dataclasses import dataclass

from quantum.domain.risk_governance.amounts.risk_monetary_amount import (
    NonNegativeRiskMeasurement,
)


@dataclass(frozen=True, slots=True)
class DailyLoss(NonNegativeRiskMeasurement):
    """
    Accumulated realized loss for the current trading day.

    Properties:
    - Always ≥ 0
    - Bound to a MoneyContext
    - Non-algebraic
    """

    @classmethod
    def nominal_type(cls) -> str:
        return "daily_loss"
