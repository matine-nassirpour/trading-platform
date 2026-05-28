from dataclasses import dataclass

from quantum.domain.risk_governance.amounts.risk_monetary_amount import (
    PositiveRiskLimit,
)


@dataclass(frozen=True, slots=True)
class DrawdownLimit(PositiveRiskLimit):
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
