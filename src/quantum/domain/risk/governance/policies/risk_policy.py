from decimal import Decimal

from quantum.domain.risk.breaches.daily_loss_breach import DailyLossBreach
from quantum.domain.risk.breaches.drawdown_breach import DrawdownBreach
from quantum.domain.risk.breaches.exposure_breach import ExposureBreach
from quantum.domain.risk.breaches.leverage_breach import LeverageBreach
from quantum.domain.risk.breaches.notional_breach import NotionalBreach
from quantum.domain.risk.core.daily_loss import DailyLoss
from quantum.domain.risk.core.drawdown import Drawdown
from quantum.domain.risk.core.equity import Equity
from quantum.domain.risk.core.exposure import Exposure
from quantum.domain.risk.core.notional import Notional
from quantum.domain.risk.limits.daily_loss_limit import DailyLossLimit
from quantum.domain.risk.limits.drawdown_limit import DrawdownLimit
from quantum.domain.risk.limits.exposure_limit import ExposureLimit
from quantum.domain.risk.limits.leverage_limit import LeverageLimit
from quantum.domain.risk.limits.notional_limit import NotionalLimit
from quantum.domain.risk.limits.risk_limits import RiskLimits
from quantum.domain.risk.limits.risk_threshold_policy import RiskThresholdPolicy
from quantum.domain.shared_kernel.errors.invariants import InvariantViolation


class RiskPolicy:
    """
    Canonical evaluation rules for desk-level risk limits.
    """

    @staticmethod
    def _is_breached(
        value: Decimal, limit: Decimal, policy: RiskThresholdPolicy
    ) -> bool:
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
        """
        Evaluates drawdown against configured limits.
        """

        limit: DrawdownLimit = limits.max_drawdown

        if RiskPolicy._is_breached(current.value, limit.value, limits.threshold_policy):
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
        """
        Evaluates daily loss against configured limits.
        """

        limit: DailyLossLimit = limits.max_daily_loss

        if RiskPolicy._is_breached(current.value, limit.value, limits.threshold_policy):
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
        """
        Evaluates notional exposure against configured limits.
        """

        limit: NotionalLimit = limits.max_notional

        if RiskPolicy._is_breached(current.value, limit.value, limits.threshold_policy):
            return NotionalBreach(
                current=current,
                limit=limit,
                policy=limits.threshold_policy,
            )

        return None

    @staticmethod
    def evaluate_exposure(
        *, current: Exposure, limits: RiskLimits
    ) -> ExposureBreach | None:
        limit: ExposureLimit = limits.max_exposure

        if RiskPolicy._is_breached(
            value=current.value,
            limit=limit.value,
            policy=limits.threshold_policy,
        ):
            return ExposureBreach(
                current=current,
                limit=limit,
                policy=limits.threshold_policy,
            )

        return None

    @staticmethod
    def evaluate_leverage(
        *,
        exposure: Exposure,
        equity: Equity,
        limits: RiskLimits,
    ) -> LeverageBreach | None:

        leverage = exposure.value / equity.value
        limit: LeverageLimit = limits.max_leverage

        if RiskPolicy._is_breached(
            value=leverage,
            limit=limit.value,
            policy=limits.threshold_policy,
        ):
            return LeverageBreach(
                exposure=exposure,
                equity=equity,
                limit=limit,
                policy=limits.threshold_policy,
            )

        return None
