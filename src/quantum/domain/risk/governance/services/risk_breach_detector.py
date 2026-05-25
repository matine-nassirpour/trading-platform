from dataclasses import dataclass

from quantum.domain.risk.governance.limits.risk_limits import RiskLimits
from quantum.domain.risk.governance.measures.daily_loss import DailyLoss
from quantum.domain.risk.governance.measures.drawdown import Drawdown
from quantum.domain.risk.governance.measures.equity import Equity
from quantum.domain.risk.governance.measures.exposure import Exposure
from quantum.domain.risk.governance.measures.notional import Notional
from quantum.domain.risk.governance.risk_state.breaches.daily_loss_breach import (
    DailyLossBreach,
)
from quantum.domain.risk.governance.risk_state.breaches.drawdown_breach import (
    DrawdownBreach,
)
from quantum.domain.risk.governance.risk_state.breaches.exposure_breach import (
    ExposureBreach,
)
from quantum.domain.risk.governance.risk_state.breaches.leverage_breach import (
    LeverageBreach,
)
from quantum.domain.risk.governance.risk_state.breaches.notional_breach import (
    NotionalBreach,
)
from quantum.domain.risk.governance.risk_state.breaches.risk_breach import RiskBreach
from quantum.domain.shared_kernel.foundation.errors.invariants import InvariantViolation
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
    def detect(
        *,
        limits: RiskLimits,
        drawdown: Drawdown,
        daily_loss: DailyLoss,
        exposure: Exposure,
        notional: Notional,
        equity: Equity,
    ) -> RiskBreachDetectionResult:
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
