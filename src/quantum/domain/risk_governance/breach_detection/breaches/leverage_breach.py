from __future__ import annotations

from dataclasses import dataclass

from quantum.domain.risk_governance.breach_detection.breaches.risk_breach import (
    RiskBreach,
)
from quantum.domain.risk_governance.breach_detection.monetary_compatibility import (
    MonetaryCompatibilityService,
)
from quantum.domain.risk_governance.breach_detection.threshold_breach_detector import (
    ThresholdBreachDetector,
)
from quantum.domain.risk_governance.limits.leverage_limit import LeverageLimit
from quantum.domain.risk_governance.limits.risk_threshold_policy import (
    RiskThresholdPolicy,
)
from quantum.domain.risk_governance.portfolio_state.equity import Equity
from quantum.domain.risk_governance.portfolio_state.exposure import Exposure
from quantum.domain.shared_kernel.foundation.errors.invariants import InvariantViolation


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

    def _validate_semantics(self) -> None:
        super()._validate_semantics()

        required_fields: tuple[tuple[str, object, type[object]], ...] = (
            ("exposure", self.exposure, Exposure),
            ("equity", self.equity, Equity),
            ("limit", self.limit, LeverageLimit),
        )

        for field_name, value, expected_type in required_fields:
            if not isinstance(value, expected_type):
                raise InvariantViolation(f"LeverageBreach.{field_name} invalid")

        MonetaryCompatibilityService.assert_same_context_and_currency(
            left=self.exposure,
            right=self.equity,
            left_label="exposure",
            right_label="equity",
        )

    # --- Factory --------------------------------------------------------------

    @staticmethod
    def detect(
        *,
        exposure: Exposure,
        equity: Equity,
        limit: LeverageLimit,
        policy: RiskThresholdPolicy,
    ) -> LeverageBreach | None:
        MonetaryCompatibilityService.assert_same_context_and_currency(
            left=exposure,
            right=equity,
            left_label="exposure",
            right_label="equity",
        )

        if equity.value <= 0:
            return None

        leverage = exposure.value / equity.value

        return ThresholdBreachDetector.detect(
            current_value=leverage,
            limit_value=limit.value,
            policy=policy,
            breach_factory=lambda: LeverageBreach(
                exposure=exposure,
                equity=equity,
                limit=limit,
                policy=policy,
            ),
        )
