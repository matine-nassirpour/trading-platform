from dataclasses import dataclass

from quantum.domain.risk_governance.amounts.risk_monetary_amount import (
    PositiveRiskLimit,
)


@dataclass(frozen=True, slots=True)
class ExposureLimit(PositiveRiskLimit):
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
