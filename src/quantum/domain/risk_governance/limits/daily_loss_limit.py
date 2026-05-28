from dataclasses import dataclass

from quantum.domain.risk_governance.amounts.risk_monetary_amount import (
    PositiveRiskLimit,
)


@dataclass(frozen=True, slots=True)
class DailyLossLimit(PositiveRiskLimit):
    """
    Maximum allowed realized loss per trading day.

    Properties:
    - Strictly positive
    - Contextual
    - Non-algebraic
    """

    @classmethod
    def nominal_type(cls) -> str:
        return "daily_loss_limit"
