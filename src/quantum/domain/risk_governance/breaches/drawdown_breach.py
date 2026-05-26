from __future__ import annotations

from dataclasses import dataclass

from quantum.domain.risk_governance.breaches.risk_breach import RiskBreach
from quantum.domain.risk_governance.limits.drawdown_limit import DrawdownLimit
from quantum.domain.risk_governance.limits.risk_threshold_policy import (
    RiskThresholdPolicy,
)
from quantum.domain.risk_governance.measures.drawdown import Drawdown
from quantum.domain.risk_governance.services.threshold_breach_detector import (
    ThresholdBreachDetector,
)
from quantum.domain.shared_kernel.foundation.errors.invariants import InvariantViolation


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

    def _validate_semantics(self) -> None:
        super()._validate_semantics()

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
        return ThresholdBreachDetector.detect(
            current_value=current.value,
            limit_value=limit.value,
            policy=policy,
            breach_factory=lambda: DrawdownBreach(
                current=current,
                limit=limit,
                policy=policy,
            ),
        )
