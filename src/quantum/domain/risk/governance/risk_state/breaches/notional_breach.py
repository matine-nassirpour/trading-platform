from __future__ import annotations

from dataclasses import dataclass

from quantum.domain.risk.governance.limits.notional_limit import NotionalLimit
from quantum.domain.risk.governance.limits.risk_threshold_policy import (
    RiskThresholdPolicy,
)
from quantum.domain.risk.governance.measures.notional import Notional
from quantum.domain.risk.governance.risk_state.breaches.risk_breach import RiskBreach
from quantum.domain.shared_kernel.foundation.errors.invariants import InvariantViolation


@dataclass(frozen=True, slots=True)
class NotionalBreach(RiskBreach):
    """
    Risk breach for notional exposure limit violation.

    Invariants:
    - kind == notional
    - current is Notional
    - limit is Notional
    - MoneyContext(current) == MoneyContext(limit)
    """

    current: Notional
    limit: NotionalLimit

    def _validate(self) -> None:
        super()._validate()

        if not isinstance(self.current, Notional):
            raise InvariantViolation("NotionalBreach.current must be a Notional")

        if not isinstance(self.limit, NotionalLimit):
            raise InvariantViolation("NotionalBreach.limit must be a NotionalLimit")

        if self.current.context != self.limit.context:
            raise InvariantViolation("Notional MoneyContext mismatch")

    # --- Factory --------------------------------------------------------------

    @staticmethod
    def detect(
        *,
        current: Notional,
        limit: NotionalLimit,
        policy: RiskThresholdPolicy,
    ) -> NotionalBreach | None:

        if not policy.is_breached(current.value, limit.value):
            return None

        return NotionalBreach(
            current=current,
            limit=limit,
            policy=policy,
        )
