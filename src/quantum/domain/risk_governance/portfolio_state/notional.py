from dataclasses import dataclass

from quantum.domain.risk_governance.amounts.risk_monetary_amount import (
    NonNegativeRiskMeasurement,
)


@dataclass(frozen=True, slots=True)
class Notional(NonNegativeRiskMeasurement):
    """
    Contractual notional amount.

    Represents the *gross contractual size* of a position or exposure.
    It is a structural quantity used for:

    - trade sizing
    - margin and fee calculations
    - regulatory and reporting purposes
    - exposure decomposition
    """

    @classmethod
    def nominal_type(cls) -> str:
        return "notional"
