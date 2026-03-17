from __future__ import annotations

from dataclasses import dataclass

from quantum.domain.risk.governance.limits.drawdown_limit import DrawdownLimit
from quantum.domain.risk.governance.limits.risk_threshold_policy import (
    RiskThresholdPolicy,
)
from quantum.domain.risk.governance.measures.drawdown import Drawdown
from quantum.domain.risk.governance.risk_state.breaches.risk_breach import RiskBreach
from quantum.domain.shared_kernel.errors.invariants import InvariantViolation


@dataclass(frozen=True, slots=True)
class DrawdownBreach(RiskBreach):
    """
    Risk breach for drawdown limit violation.

    Invariants:
    - kind == drawdown
    - current is Drawdown
    - limit is DrawdownLimit
    - MoneyContext(current) == MoneyContext(limit)
    """

    current: Drawdown
    limit: DrawdownLimit

    def _validate(self) -> None:
        super()._validate()

        if not isinstance(self.current, Drawdown):
            raise InvariantViolation("DrawdownBreach.current must be a Drawdown")

        if not isinstance(self.limit, DrawdownLimit):
            raise InvariantViolation("DrawdownBreach.limit must be a DrawdownLimit")

        if self.current.context != self.limit.context:
            raise InvariantViolation("Drawdown MoneyContext mismatch")

    # --- Factory --------------------------------------------------------------

    @staticmethod
    def detect(
        *,
        current: Drawdown,
        limit: DrawdownLimit,
        policy: RiskThresholdPolicy,
    ) -> DrawdownBreach | None:

        if not policy.is_breached(current.value, limit.value):
            return None

        return DrawdownBreach(
            current=current,
            limit=limit,
            policy=policy,
        )
