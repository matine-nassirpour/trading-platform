from __future__ import annotations

from typing import Protocol, runtime_checkable

from quantum.domain.risk.limits.risk_limits import RiskLimits


@runtime_checkable
class RiskLimitsProvider(Protocol):
    """
    Provides desk/account risk limits (policy configuration).
    """

    def get_limits(self) -> RiskLimits:
        raise NotImplementedError
