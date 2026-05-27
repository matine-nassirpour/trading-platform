from __future__ import annotations

from dataclasses import dataclass

from quantum.domain.risk_governance.breaches.risk_breach import RiskBreach
from quantum.domain.risk_governance.limits.risk_threshold_policy import (
    RiskThresholdPolicy,
)
from quantum.domain.risk_governance.measures.equity import Equity
from quantum.domain.shared_kernel.foundation.errors.invariants import InvariantViolation


@dataclass(frozen=True, slots=True)
class NonPositiveEquityBreach(RiskBreach):
    """
    Risk breach raised when equity is zero or negative.

    This is NOT a leverage breach.

    Doctrine:
    - leverage requires strictly positive equity;
    - equity <= 0 represents capital insolvency / account failure state;
    - this breach must be handled independently from leverage limits.
    """

    equity: Equity

    def _validate_semantics(self) -> None:
        super()._validate_semantics()

        if not isinstance(self.equity, Equity):
            raise InvariantViolation("NonPositiveEquityBreach.equity must be Equity")

        if self.equity.value > 0:
            raise InvariantViolation("NonPositiveEquityBreach requires equity <= 0")

    @staticmethod
    def detect(
        *,
        equity: Equity,
        policy: RiskThresholdPolicy,
    ) -> NonPositiveEquityBreach | None:
        if not isinstance(equity, Equity):
            raise InvariantViolation("equity must be Equity")

        if equity.value > 0:
            return None

        return NonPositiveEquityBreach(
            equity=equity,
            policy=policy,
        )
