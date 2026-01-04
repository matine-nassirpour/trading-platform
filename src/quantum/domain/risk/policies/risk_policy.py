from quantum.domain.risk.value_objects.risk_breach import RiskBreach
from quantum.domain.risk.value_objects.risk_breach_kind import RiskBreachKind
from quantum.domain.risk.value_objects.risk_limits import RiskLimits
from quantum.domain.shared.primitives.monetary_value_object import MonetaryValueObject


class RiskPolicy:
    """
    Canonical evaluation rules for desk-level risk limits.
    """

    @staticmethod
    def evaluate_drawdown(
        *,
        current_drawdown: MonetaryValueObject,
        limits: RiskLimits,
    ) -> RiskBreach | None:
        if current_drawdown.value >= limits.max_drawdown.value:
            return RiskBreach(
                kind=RiskBreachKind.drawdown(),
                current=current_drawdown,
                limit=limits.max_drawdown,
            )
        return None

    @staticmethod
    def evaluate_notional(
        *,
        notional: MonetaryValueObject,
        limits: RiskLimits,
    ) -> RiskBreach | None:
        if notional.value >= limits.max_notional.value:
            return RiskBreach(
                kind=RiskBreachKind.notional(),
                current=notional,
                limit=limits.max_notional,
            )
        return None

    @staticmethod
    def evaluate_daily_loss(
        *,
        daily_loss: MonetaryValueObject,
        limits: RiskLimits,
    ) -> RiskBreach | None:
        if daily_loss.value >= limits.max_daily_loss.value:
            return RiskBreach(
                kind=RiskBreachKind.daily_loss(),
                current=daily_loss,
                limit=limits.max_daily_loss,
            )
        return None
