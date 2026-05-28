from dataclasses import dataclass

from quantum.domain.risk_governance.amounts.risk_monetary_amount import (
    NonNegativeRiskMeasurement,
)


@dataclass(frozen=True, slots=True)
class Exposure(NonNegativeRiskMeasurement):
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

    @classmethod
    def nominal_type(cls) -> str:
        return "exposure"
