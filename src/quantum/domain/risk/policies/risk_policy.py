from quantum.domain.risk.value_objects.risk_breach import RiskBreach
from quantum.domain.risk.value_objects.risk_breach_kind import RiskBreachKind
from quantum.domain.risk.value_objects.risk_limits import RiskLimits
from quantum.domain.risk.value_objects.risk_threshold_policy import RiskThresholdPolicy
from quantum.domain.shared_kernel.primitives.monetary_amount import MonetaryAmount


class RiskPolicy:
    """
    Canonical evaluation rules for desk-level risk limits.
    """

    @staticmethod
    def _breached(
        *,
        current: MonetaryAmount,
        limit: MonetaryAmount,
        policy: RiskThresholdPolicy,
    ) -> bool:
        """
        Evaluates whether a risk limit is breached according to the configured
        threshold policy.
        """
        if policy == RiskThresholdPolicy.inclusive():
            return current.value >= limit.value

        return current.value > limit.value

    # --- Public evaluation rules ----------------------------------------------

    @staticmethod
    def evaluate_drawdown(
        *,
        current_drawdown: MonetaryAmount,
        limits: RiskLimits,
    ) -> RiskBreach | None:
        if RiskPolicy._breached(
            current=current_drawdown,
            limit=limits.max_drawdown,
            policy=limits.threshold_policy,
        ):
            return RiskBreach(
                kind=RiskBreachKind.drawdown(),
                current=current_drawdown,
                limit=limits.max_drawdown,
            )

        return None

    @staticmethod
    def evaluate_notional(
        *,
        notional: MonetaryAmount,
        limits: RiskLimits,
    ) -> RiskBreach | None:
        if RiskPolicy._breached(
            current=notional,
            limit=limits.max_notional,
            policy=limits.threshold_policy,
        ):
            return RiskBreach(
                kind=RiskBreachKind.notional(),
                current=notional,
                limit=limits.max_notional,
            )

        return None

    @staticmethod
    def evaluate_daily_loss(
        *,
        daily_loss: MonetaryAmount,
        limits: RiskLimits,
    ) -> RiskBreach | None:
        if RiskPolicy._breached(
            current=daily_loss,
            limit=limits.max_daily_loss,
            policy=limits.threshold_policy,
        ):
            return RiskBreach(
                kind=RiskBreachKind.daily_loss(),
                current=daily_loss,
                limit=limits.max_daily_loss,
            )

        return None
