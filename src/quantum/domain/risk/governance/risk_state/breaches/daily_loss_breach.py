from __future__ import annotations

from dataclasses import dataclass

from quantum.domain.risk.governance.limits.daily_loss_limit import DailyLossLimit
from quantum.domain.risk.governance.limits.risk_threshold_policy import (
    RiskThresholdPolicy,
)
from quantum.domain.risk.governance.measures.daily_loss import DailyLoss
from quantum.domain.risk.governance.risk_state.breaches.risk_breach import RiskBreach
from quantum.domain.shared_kernel.errors.invariants import InvariantViolation


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

    def _validate(self) -> None:
        super()._validate()

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

        if not policy.is_breached(current.value, limit.value):
            return None

        return DailyLossBreach(
            current=current,
            limit=limit,
            policy=policy,
        )
