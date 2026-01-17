from decimal import Decimal

from quantum.domain.risk.breaches.daily_loss_breach import DailyLossBreach
from quantum.domain.risk.breaches.drawdown_breach import DrawdownBreach
from quantum.domain.risk.breaches.notional_breach import NotionalBreach
from quantum.domain.risk.core.daily_loss import DailyLoss
from quantum.domain.risk.core.drawdown import Drawdown
from quantum.domain.risk.core.notional import Notional
from quantum.domain.risk.limits.daily_loss_limit import DailyLossLimit
from quantum.domain.risk.limits.drawdown_limit import DrawdownLimit
from quantum.domain.risk.limits.risk_limits import RiskLimits
from quantum.domain.risk.limits.risk_threshold_policy import RiskThresholdPolicy
from quantum.domain.shared_kernel.errors.invariants import InvariantViolation


class RiskPolicy:
    """
    Canonical evaluation rules for desk-level risk limits.
    """

    @staticmethod
    def _breach(value: Decimal, limit: Decimal, policy: RiskThresholdPolicy) -> bool:
        mode = policy.value

        if mode == "inclusive":
            return value >= limit

        if mode == "exclusive":
            return value > limit

        raise InvariantViolation(f"Unknown RiskThresholdPolicy: {mode}")

    # --- Public evaluation rules ----------------------------------------------

    @staticmethod
    def evaluate_drawdown(
        *, current: Drawdown, limits: RiskLimits
    ) -> DrawdownBreach | None:
        limit: DrawdownLimit = limits.max_drawdown

        if RiskPolicy._breach(current.value, limit.value, limits.threshold_policy):
            return DrawdownBreach(
                current=current,
                limit=limit,
                policy=limits.threshold_policy,
            )

        return None

    @staticmethod
    def evaluate_daily_loss(
        *, current: DailyLoss, limits: RiskLimits
    ) -> DailyLossBreach | None:
        limit: DailyLossLimit = limits.max_daily_loss

        if RiskPolicy._breach(current.value, limit.value, limits.threshold_policy):
            return DailyLossBreach(
                current=current,
                limit=limit,
                policy=limits.threshold_policy,
            )

        return None

    @staticmethod
    def evaluate_notional(
        *, current: Notional, limits: RiskLimits
    ) -> NotionalBreach | None:
        limit: Notional = limits.max_notional

        if RiskPolicy._breach(current.value, limit.value, limits.threshold_policy):
            return NotionalBreach(
                current=current,
                limit=limit,
                policy=limits.threshold_policy,
            )

        return None
