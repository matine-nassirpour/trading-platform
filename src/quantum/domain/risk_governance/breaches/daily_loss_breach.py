from __future__ import annotations

from dataclasses import dataclass

from quantum.domain.risk_governance.breaches.risk_breach import RiskBreach
from quantum.domain.risk_governance.limits.daily_loss_limit import DailyLossLimit
from quantum.domain.risk_governance.limits.risk_threshold_policy import (
    RiskThresholdPolicy,
)
from quantum.domain.risk_governance.measures.daily_loss import DailyLoss
from quantum.domain.risk_governance.services.threshold_breach_detector import (
    ThresholdBreachDetector,
)
from quantum.domain.shared_kernel.foundation.errors.invariants import InvariantViolation


@dataclass(frozen=True, slots=True)
class DailyLossBreach(RiskBreach):
    """
    Risk breach for daily realized loss limit violation.

    Invariants:
    - kind == daily_loss
    - current is DailyLoss
    - limit is DailyLossLimit
    - MoneyContext(current) == MoneyContext(limit)
    """

    current: DailyLoss
    limit: DailyLossLimit

    def _validate_semantics(self) -> None:
        super()._validate_semantics()

        if not isinstance(self.current, DailyLoss):
            raise InvariantViolation("DailyLossBreach.current must be a DailyLoss")

        if not isinstance(self.limit, DailyLossLimit):
            raise InvariantViolation("DailyLossBreach.limit must be a DailyLossLimit")

        if self.current.context != self.limit.context:
            raise InvariantViolation("DailyLoss MoneyContext mismatch")

    # --- Factory --------------------------------------------------------------

    @staticmethod
    def detect(
        *,
        current: DailyLoss,
        limit: DailyLossLimit,
        policy: RiskThresholdPolicy,
    ) -> DailyLossBreach | None:
        return ThresholdBreachDetector.detect(
            current_value=current.value,
            limit_value=limit.value,
            policy=policy,
            breach_factory=lambda: DailyLossBreach(
                current=current,
                limit=limit,
                policy=policy,
            ),
        )
