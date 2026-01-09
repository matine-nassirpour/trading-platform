from quantum.domain.risk.value_objects.risk_breach import RiskBreach
from quantum.domain.risk.value_objects.risk_breach_kind import RiskBreachKind
from quantum.domain.risk.value_objects.risk_limits import RiskLimits
from quantum.domain.risk.value_objects.risk_threshold_policy import RiskThresholdPolicy
from quantum.domain.shared_kernel.errors.invariants import InvariantViolation
from quantum.domain.shared_kernel.money.contextual_monetary_amount import (
    ContextualMonetaryAmount,
)
from quantum.domain.shared_kernel.policies.domain_policy import DomainPolicy


class RiskPolicy(DomainPolicy):
    """
    Canonical evaluation rules for desk-level risk limits.
    """

    @staticmethod
    def _breached(
        *,
        current: ContextualMonetaryAmount,
        limit: ContextualMonetaryAmount,
        policy: RiskThresholdPolicy,
    ) -> bool:
        if not isinstance(current, ContextualMonetaryAmount):
            raise InvariantViolation("RiskPolicy requires ContextualMonetaryAmount")

        if not isinstance(limit, ContextualMonetaryAmount):
            raise InvariantViolation("RiskPolicy requires ContextualMonetaryAmount")

        if current.context != limit.context:
            raise InvariantViolation(
                f"MoneyContext mismatch: {current.context} vs {limit.context}"
            )

        if policy == RiskThresholdPolicy.inclusive():
            return current.value >= limit.value

        return current.value > limit.value

    # --- Public evaluation rules ----------------------------------------------

    @staticmethod
    def evaluate_drawdown(
        *,
        current_drawdown: ContextualMonetaryAmount,
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
        notional: ContextualMonetaryAmount,
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
        daily_loss: ContextualMonetaryAmount,
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
