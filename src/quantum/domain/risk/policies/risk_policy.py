from decimal import Decimal

from quantum.domain.risk.value_objects.daily_loss import DailyLoss
from quantum.domain.risk.value_objects.daily_loss_limit import DailyLossLimit
from quantum.domain.risk.value_objects.drawdown import Drawdown
from quantum.domain.risk.value_objects.drawdown_limit import DrawdownLimit
from quantum.domain.risk.value_objects.notional import Notional
from quantum.domain.risk.value_objects.risk_breach import RiskBreach
from quantum.domain.risk.value_objects.risk_breach_kind import RiskBreachKind
from quantum.domain.risk.value_objects.risk_limits import RiskLimits
from quantum.domain.risk.value_objects.risk_threshold_policy import RiskThresholdPolicy
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
    ) -> RiskBreach | None:
        if not isinstance(current, Drawdown):
            raise InvariantViolation("evaluate_drawdown requires Drawdown")

        limit: DrawdownLimit = limits.max_drawdown

        if RiskPolicy._breach(current.value, limit.value, limits.threshold_policy):
            return RiskBreach(
                kind=RiskBreachKind.drawdown(),
                current=current,
                limit=limit,
                policy=limits.threshold_policy,
            )

        return None

    @staticmethod
    def evaluate_notional(
        *, current: Notional, limits: RiskLimits
    ) -> RiskBreach | None:
        if not isinstance(current, Notional):
            raise InvariantViolation("evaluate_notional requires Notional")

        limit: Notional = limits.max_notional

        if RiskPolicy._breach(current.value, limit.value, limits.threshold_policy):
            return RiskBreach(
                kind=RiskBreachKind.notional(),
                current=current,
                limit=limit,
                policy=limits.threshold_policy,
            )

        return None

    @staticmethod
    def evaluate_daily_loss(
        *, current: DailyLoss, limits: RiskLimits
    ) -> RiskBreach | None:
        if not isinstance(current, DailyLoss):
            raise InvariantViolation("evaluate_daily_loss requires DailyLoss")

        limit: DailyLossLimit = limits.max_daily_loss

        if RiskPolicy._breach(current.value, limit.value, limits.threshold_policy):
            return RiskBreach(
                kind=RiskBreachKind.daily_loss(),
                current=current,
                limit=limit,
                policy=limits.threshold_policy,
            )

        return None
