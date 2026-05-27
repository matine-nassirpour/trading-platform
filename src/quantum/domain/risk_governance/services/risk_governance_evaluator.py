from dataclasses import dataclass

from quantum.domain.risk_governance.breaches.risk_breach import RiskBreach
from quantum.domain.risk_governance.limits.risk_limits import RiskLimits
from quantum.domain.risk_governance.services.equity_evolution import (
    EquityEvolutionService,
)
from quantum.domain.risk_governance.services.risk_breach_detector import (
    RiskBreachDetector,
)
from quantum.domain.risk_governance.states.risk_governance_initialized_state import (
    RiskGovernanceInitializedState,
)
from quantum.domain.risk_governance.states.risk_snapshot import RiskSnapshot
from quantum.domain.shared_kernel.foundation.errors.invariants import (
    CurrencyMismatch,
    InvariantViolation,
)
from quantum.domain.shared_kernel.modeling.monetary.pnl import RealizedPnL
from quantum.domain.shared_kernel.modeling.services.domain_service import DomainService
from quantum.domain.shared_kernel.modeling.value_objects.value_object import ValueObject


@dataclass(frozen=True, slots=True)
class RiskGovernanceEvaluation(ValueObject):
    new_snapshot: RiskSnapshot
    breaches: tuple[RiskBreach, ...]

    def _validate_semantics(self) -> None:
        if not isinstance(self.new_snapshot, RiskSnapshot):
            raise InvariantViolation("new_snapshot must be RiskSnapshot")

        if not isinstance(self.breaches, tuple):
            raise InvariantViolation("breaches must be tuple[RiskBreach, ...]")

        for breach in self.breaches:
            if not isinstance(breach, RiskBreach):
                raise InvariantViolation("breaches must contain only RiskBreach")


class RiskGovernanceEvaluator(DomainService):
    __slots__ = ()

    @staticmethod
    def _validate_register_pnl_inputs(
        *,
        limits: RiskLimits,
        snapshot: RiskSnapshot,
        pnl: RealizedPnL,
    ) -> None:
        expected_context = limits.context
        expected_currency = limits.context.reporting_currency

        for name, value in (
            ("snapshot.equity", snapshot.equity),
            ("snapshot.equity_peak", snapshot.equity_peak),
            ("snapshot.drawdown", snapshot.drawdown),
            ("snapshot.daily_loss", snapshot.daily_loss),
            ("snapshot.exposure", snapshot.exposure),
            ("snapshot.notional", snapshot.notional),
            ("pnl", pnl),
        ):
            if value.context != expected_context:
                raise InvariantViolation(f"{name} MoneyContext mismatch")

            if value.currency != expected_currency:
                raise CurrencyMismatch(
                    f"{name} currency must equal "
                    "RiskLimits.context.reporting_currency"
                )

    @staticmethod
    def evaluate_register_pnl(
        *,
        state: RiskGovernanceInitializedState,
        pnl: RealizedPnL,
    ) -> RiskGovernanceEvaluation:
        RiskGovernanceEvaluator._validate_register_pnl_inputs(
            limits=state.limits,
            snapshot=state.snapshot,
            pnl=pnl,
        )

        evolution = EquityEvolutionService.evolve(
            current_equity=state.snapshot.equity,
            current_peak=state.snapshot.equity_peak,
            pnl=pnl,
        )

        new_snapshot = RiskSnapshot(
            equity=evolution.new_equity,
            equity_peak=evolution.new_equity_peak,
            drawdown=evolution.drawdown,
            daily_loss=state.snapshot.daily_loss,
            exposure=state.snapshot.exposure,
            notional=state.snapshot.notional,
        )

        detection = RiskBreachDetector.detect(
            limits=state.limits,
            drawdown=new_snapshot.drawdown,
            daily_loss=new_snapshot.daily_loss,
            exposure=new_snapshot.exposure,
            notional=new_snapshot.notional,
            equity=new_snapshot.equity,
        )

        return RiskGovernanceEvaluation(
            new_snapshot=new_snapshot,
            breaches=detection.breaches,
        )
