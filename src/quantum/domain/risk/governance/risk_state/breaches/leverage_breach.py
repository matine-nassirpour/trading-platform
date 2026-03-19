from __future__ import annotations

from dataclasses import dataclass

from quantum.domain.risk.governance.limits.leverage_limit import LeverageLimit
from quantum.domain.risk.governance.limits.risk_threshold_policy import (
    RiskThresholdPolicy,
)
from quantum.domain.risk.governance.measures.equity import Equity
from quantum.domain.risk.governance.measures.exposure import Exposure
from quantum.domain.risk.governance.risk_state.breaches.risk_breach import RiskBreach
from quantum.domain.shared_kernel.foundation.errors.invariants import (
    CurrencyMismatch,
    InvariantViolation,
)


@dataclass(frozen=True, slots=True)
class LeverageBreach(RiskBreach):
    """
    Risk breach raised when effective leverage exceeds allowed limit.

    Leverage is defined as:
        exposure / equity

    This breach indicates excessive capital amplification.
    """

    exposure: Exposure
    equity: Equity
    limit: LeverageLimit

    def _validate(self) -> None:
        super()._validate()

        if not isinstance(self.exposure, Exposure):
            raise InvariantViolation("LeverageBreach.exposure must be RiskExposure")

        if not isinstance(self.limit, LeverageLimit):
            raise InvariantViolation("LeverageBreach.limit must be LeverageLimit")

        if not isinstance(self.equity, Equity):
            raise InvariantViolation("LeverageBreach.equity must be Equity")

        if self.equity.value <= 0:
            raise InvariantViolation("Equity must be strictly positive")

        if self.exposure.context != self.equity.context:
            raise InvariantViolation("Exposure context mismatch")

        if self.exposure.currency != self.equity.currency:
            raise CurrencyMismatch("Exposure currency mismatch")

    # --- Factory --------------------------------------------------------------

    @staticmethod
    def detect(
        *,
        exposure: Exposure,
        equity: Equity,
        limit: LeverageLimit,
        policy: RiskThresholdPolicy,
    ) -> LeverageBreach | None:

        leverage = exposure.value / equity.value

        if not policy.is_breached(leverage, limit.value):
            return None

        return LeverageBreach(
            exposure=exposure,
            equity=equity,
            limit=limit,
            policy=policy,
        )
