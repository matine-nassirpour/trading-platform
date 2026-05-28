from dataclasses import dataclass

from quantum.domain.risk_governance.amounts.risk_monetary_amount import (
    NonNegativeRiskMeasurement,
)


@dataclass(frozen=True, slots=True)
class Drawdown(NonNegativeRiskMeasurement):
    """
    Drawdown = equity_peak − equity.

    Properties:
    - Always ≥ 0
    - Bound to a MoneyContext
    - Non-algebraic (cannot be added/subtracted)
    """

    @classmethod
    def nominal_type(cls) -> str:
        return "drawdown"
