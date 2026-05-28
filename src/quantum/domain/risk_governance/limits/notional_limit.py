from dataclasses import dataclass

from quantum.domain.risk_governance.amounts.risk_monetary_amount import (
    PositiveRiskLimit,
)


@dataclass(frozen=True, slots=True)
class NotionalLimit(PositiveRiskLimit):
    """
    Maximum allowed notional exposure.

    This represents a HARD constraint on the contractual size
    of positions, independent of risk-weighting or netting.

    NotionalLimit is a governance rule, not a measurement.
    """

    @classmethod
    def nominal_type(cls) -> str:
        return "notional_limit"
