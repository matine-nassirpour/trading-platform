from quantum.application.ports.outbound.financial_state_provider import (
    FinancialStateProvider,
)
from quantum.domain.risk.breaches.daily_loss_breach import DailyLossBreach
from quantum.domain.risk.breaches.drawdown_breach import DrawdownBreach
from quantum.domain.risk.breaches.exposure_breach import ExposureBreach
from quantum.domain.risk.breaches.leverage_breach import LeverageBreach
from quantum.domain.risk.breaches.notional_breach import NotionalBreach
from quantum.domain.risk.breaches.risk_breach import RiskBreach
from quantum.domain.risk.limits.risk_limits import RiskLimits


class RiskEvaluationService:
    """
    Orchestrates detection of all risk breaches.
    """

    def __init__(self, financials: FinancialStateProvider) -> None:
        self._financials = financials

    def evaluate(self, limits: RiskLimits) -> list[RiskBreach]:
        policy = limits.threshold_policy

        breaches: list[RiskBreach] = []

        drawdown = DrawdownBreach.detect(
            current=self._financials.current_drawdown(),
            limit=limits.max_drawdown,
            policy=policy,
        )
        if drawdown:
            breaches.append(drawdown)

        daily = DailyLossBreach.detect(
            current=self._financials.current_daily_loss(),
            limit=limits.max_daily_loss,
            policy=policy,
        )
        if daily:
            breaches.append(daily)

        notional = NotionalBreach.detect(
            current=self._financials.current_notional(),
            limit=limits.max_notional,
            policy=policy,
        )
        if notional:
            breaches.append(notional)

        exposure = ExposureBreach.detect(
            current=self._financials.current_exposure(),
            limit=limits.max_exposure,
            policy=policy,
        )
        if exposure:
            breaches.append(exposure)

        leverage = LeverageBreach.detect(
            exposure=self._financials.current_exposure(),
            equity=self._financials.current_equity(),
            limit=limits.max_leverage,
            policy=policy,
        )
        if leverage:
            breaches.append(leverage)

        return breaches
