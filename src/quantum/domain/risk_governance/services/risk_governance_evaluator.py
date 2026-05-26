from dataclasses import dataclass

from quantum.domain.risk_governance.breaches.risk_breach import RiskBreach
from quantum.domain.risk_governance.measures.daily_loss import DailyLoss
from quantum.domain.risk_governance.measures.equity import Equity
from quantum.domain.risk_governance.measures.exposure import Exposure
from quantum.domain.risk_governance.measures.notional import Notional
from quantum.domain.risk_governance.services.equity_evolution import (
    EquityEvolutionService,
)
from quantum.domain.risk_governance.services.risk_breach_detector import (
    RiskBreachDetector,
)
from quantum.domain.risk_governance.services.risk_input_validator import (
    RiskInputValidator,
)
from quantum.domain.risk_governance.states.risk_governance_initialized_state import (
    RiskGovernanceInitializedState,
)
from quantum.domain.shared_kernel.foundation.errors.invariants import InvariantViolation
from quantum.domain.shared_kernel.modeling.monetary.pnl import RealizedPnL
from quantum.domain.shared_kernel.modeling.services.domain_service import DomainService
from quantum.domain.shared_kernel.modeling.value_objects.value_object import ValueObject


@dataclass(frozen=True, slots=True)
class RiskGovernanceEvaluation(ValueObject):
    new_equity: Equity
    new_equity_peak: Equity
    breaches: tuple[RiskBreach, ...]

    def _validate_semantics(self) -> None:
        if not isinstance(self.new_equity, Equity):
            raise InvariantViolation("new_equity must be Equity")

        if not isinstance(self.new_equity_peak, Equity):
            raise InvariantViolation("new_equity_peak must be Equity")

        if not isinstance(self.breaches, tuple):
            raise InvariantViolation("breaches must be tuple[RiskBreach, ...]")

        for breach in self.breaches:
            if not isinstance(breach, RiskBreach):
                raise InvariantViolation("breaches must contain only RiskBreach")


class RiskGovernanceEvaluator(DomainService):
    __slots__ = ()

    @staticmethod
    def evaluate_register_pnl(
        *,
        state: RiskGovernanceInitializedState,
        pnl: RealizedPnL,
        daily_loss: DailyLoss,
        exposure: Exposure,
        notional: Notional,
    ) -> RiskGovernanceEvaluation:
        RiskInputValidator.validate_register_pnl_inputs(
            limits=state.limits,
            equity=state.equity,
            pnl=pnl,
            daily_loss=daily_loss,
            exposure=exposure,
            notional=notional,
        )

        evolution = EquityEvolutionService.evolve(
            current_equity=state.equity,
            current_peak=state.equity_peak,
            pnl=pnl,
        )

        detection = RiskBreachDetector.detect(
            limits=state.limits,
            drawdown=evolution.drawdown,
            daily_loss=daily_loss,
            exposure=exposure,
            notional=notional,
            equity=evolution.new_equity,
        )

        return RiskGovernanceEvaluation(
            new_equity=evolution.new_equity,
            new_equity_peak=evolution.new_equity_peak,
            breaches=detection.breaches,
        )
