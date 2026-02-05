from typing import Protocol, runtime_checkable

from quantum.domain.risk.limits.risk_limits import RiskLimits


@runtime_checkable
class RiskLimitsRepository(Protocol):
    """
    Provides desk/account risk limits (policy configuration).
    """

    def current_limits(self) -> RiskLimits:
        raise NotImplementedError
