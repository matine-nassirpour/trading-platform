from dataclasses import dataclass

from quantum.domain.risk_governance.breaches.daily_loss_breach import DailyLossBreach
from quantum.domain.risk_governance.breaches.drawdown_breach import DrawdownBreach
from quantum.domain.risk_governance.breaches.exposure_breach import ExposureBreach
from quantum.domain.risk_governance.breaches.leverage_breach import LeverageBreach
from quantum.domain.risk_governance.breaches.non_positive_equity_breach import (
    NonPositiveEquityBreach,
)
from quantum.domain.risk_governance.breaches.notional_breach import NotionalBreach
from quantum.domain.risk_governance.breaches.risk_breach import RiskBreach
from quantum.domain.risk_governance.limits.risk_limits import RiskLimits
from quantum.domain.risk_governance.measures.daily_loss import DailyLoss
from quantum.domain.risk_governance.measures.drawdown import Drawdown
from quantum.domain.risk_governance.measures.equity import Equity
from quantum.domain.risk_governance.measures.exposure import Exposure
from quantum.domain.risk_governance.measures.notional import Notional
from quantum.domain.shared_kernel.foundation.errors.invariants import (
    CurrencyMismatch,
    InvariantViolation,
)
from quantum.domain.shared_kernel.modeling.services.domain_service import DomainService
from quantum.domain.shared_kernel.modeling.value_objects.value_object import ValueObject


@dataclass(frozen=True, slots=True)
class RiskBreachDetectionResult(ValueObject):
    breaches: tuple[RiskBreach, ...]

    def _validate_semantics(self) -> None:
        if not isinstance(self.breaches, tuple):
            raise InvariantViolation("breaches must be tuple[RiskBreach, ...]")

        for breach in self.breaches:
            if not isinstance(breach, RiskBreach):
                raise InvariantViolation("breaches must contain only RiskBreach")


class RiskBreachDetector(DomainService):
    __slots__ = ()

    @staticmethod
    def _validate_inputs(
        *,
        limits: RiskLimits,
        drawdown: Drawdown,
        daily_loss: DailyLoss,
        exposure: Exposure,
        notional: Notional,
        equity: Equity,
    ) -> None:
        if not isinstance(limits, RiskLimits):
            raise InvariantViolation("limits must be RiskLimits")

        expected_context = limits.context
        expected_currency = limits.context.reporting_currency

        values = (
            ("drawdown", drawdown, Drawdown),
            ("daily_loss", daily_loss, DailyLoss),
            ("exposure", exposure, Exposure),
            ("notional", notional, Notional),
            ("equity", equity, Equity),
        )

        for name, value, expected_type in values:
            if not isinstance(value, expected_type):
                raise InvariantViolation(
                    f"{name} must be {expected_type.__name__}, "
                    f"got {type(value).__name__}"
                )

            if value.context != expected_context:
                raise InvariantViolation(
                    f"{name} MoneyContext mismatch with RiskLimits.context"
                )

            if value.currency != expected_currency:
                raise CurrencyMismatch(
                    f"{name} currency must equal RiskLimits.context.reporting_currency"
                )

    @staticmethod
    def detect(
        *,
        limits: RiskLimits,
        drawdown: Drawdown,
        daily_loss: DailyLoss,
        exposure: Exposure,
        notional: Notional,
        equity: Equity,
    ) -> RiskBreachDetectionResult:
        RiskBreachDetector._validate_inputs(
            limits=limits,
            drawdown=drawdown,
            daily_loss=daily_loss,
            exposure=exposure,
            notional=notional,
            equity=equity,
        )

        policy = limits.threshold_policy

        candidates = (
            DrawdownBreach.detect(
                current=drawdown,
                limit=limits.max_drawdown,
                policy=policy,
            ),
            DailyLossBreach.detect(
                current=daily_loss,
                limit=limits.max_daily_loss,
                policy=policy,
            ),
            ExposureBreach.detect(
                current=exposure,
                limit=limits.max_exposure,
                policy=policy,
            ),
            NotionalBreach.detect(
                current=notional,
                limit=limits.max_notional,
                policy=policy,
            ),
            NonPositiveEquityBreach.detect(
                equity=equity,
                policy=policy,
            ),
            LeverageBreach.detect(
                exposure=exposure,
                equity=equity,
                limit=limits.max_leverage,
                policy=policy,
            ),
        )

        return RiskBreachDetectionResult(
            breaches=tuple(breach for breach in candidates if breach is not None)
        )
