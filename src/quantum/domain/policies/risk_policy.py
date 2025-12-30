from quantum.domain.model.value_objects.money import Money
from quantum.domain.model.value_objects.risk_breach import RiskBreach
from quantum.domain.model.value_objects.risk_limits import RiskLimits


class RiskPolicy:
    """
    Canonical evaluation rules for desk-level risk limits.
    """

    @staticmethod
    def evaluate_drawdown(
        *,
        current_drawdown: Money,
        limits: RiskLimits,
    ) -> RiskBreach | None:
        if current_drawdown.value >= limits.max_drawdown.value:
            return RiskBreach(
                kind="drawdown",
                current=current_drawdown,
                limit=limits.max_drawdown,
            )
        return None

    @staticmethod
    def evaluate_notional(
        *,
        notional: Money,
        limits: RiskLimits,
    ) -> RiskBreach | None:
        if notional.value >= limits.max_notional.value:
            return RiskBreach(
                kind="notional",
                current=notional,
                limit=limits.max_notional,
            )
        return None

    @staticmethod
    def evaluate_daily_loss(
        *,
        daily_loss: Money,
        limits: RiskLimits,
    ) -> RiskBreach | None:
        if daily_loss.value >= limits.max_daily_loss.value:
            return RiskBreach(
                kind="daily_loss",
                current=daily_loss,
                limit=limits.max_daily_loss,
            )
        return None
