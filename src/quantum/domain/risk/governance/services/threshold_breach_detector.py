from typing import TypeVar

from quantum.domain.risk.governance.limits.risk_threshold_policy import (
    RiskThresholdPolicy,
)
from quantum.domain.risk.governance.risk_state.breaches.risk_breach import RiskBreach
from quantum.domain.shared_kernel.modeling.services.domain_service import DomainService

B = TypeVar("B", bound=RiskBreach)


class ThresholdBreachDetector(DomainService):
    """
    Pure threshold breach detection policy.

    Centralizes the canonical:
        if breached -> build breach
        else -> None
    pattern.
    """

    __slots__ = ()

    @staticmethod
    def detect(
        *,
        current_value,
        limit_value,
        policy: RiskThresholdPolicy,
        breach_factory,
    ) -> B | None:
        if not policy.is_breached(current_value, limit_value):
            return None

        return breach_factory()
