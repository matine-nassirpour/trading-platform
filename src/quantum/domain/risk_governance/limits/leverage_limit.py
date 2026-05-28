from dataclasses import dataclass

from quantum.domain.risk_governance.amounts.risk_scalar_limit import (
    PositiveRiskScalarLimit,
)


@dataclass(frozen=True, slots=True)
class LeverageLimit(PositiveRiskScalarLimit):
    """
    Maximum allowed leverage.

    Example:
        5.0 → 5x leverage
    """

    @classmethod
    def nominal_type(cls) -> str:
        return "leverage_limit"
