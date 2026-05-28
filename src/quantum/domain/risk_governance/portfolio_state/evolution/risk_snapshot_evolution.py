from dataclasses import dataclass

from quantum.domain.risk_governance.portfolio_state.evolution.daily_loss_evolution import (
    DailyLossEvolutionService,
)
from quantum.domain.risk_governance.portfolio_state.evolution.equity_evolution import (
    EquityEvolutionService,
)
from quantum.domain.risk_governance.portfolio_state.risk_snapshot import RiskSnapshot
from quantum.domain.shared_kernel.modeling.monetary.pnl import RealizedPnL
from quantum.domain.shared_kernel.modeling.services.domain_service import DomainService
from quantum.domain.shared_kernel.modeling.value_objects.value_object import ValueObject


@dataclass(frozen=True, slots=True)
class RiskSnapshotEvolutionResult(ValueObject):
    snapshot: RiskSnapshot

    def _validate_semantics(self) -> None:
        if not isinstance(self.snapshot, RiskSnapshot):
            raise TypeError("snapshot must be RiskSnapshot")


class RiskSnapshotEvolutionService(DomainService):
    __slots__ = ()

    @staticmethod
    def evolve_after_realized_pnl(
        *,
        current_snapshot: RiskSnapshot,
        pnl: RealizedPnL,
    ) -> RiskSnapshotEvolutionResult:
        evolution = EquityEvolutionService.evolve(
            current_equity=current_snapshot.equity,
            current_peak=current_snapshot.equity_peak,
            pnl=pnl,
        )

        new_daily_loss = DailyLossEvolutionService.evolve(
            current_daily_loss=current_snapshot.daily_loss,
            pnl=pnl,
        )

        return RiskSnapshotEvolutionResult(
            snapshot=RiskSnapshot(
                equity=evolution.new_equity,
                equity_peak=evolution.new_equity_peak,
                drawdown=evolution.drawdown,
                daily_loss=new_daily_loss,
                exposure=current_snapshot.exposure,
                notional=current_snapshot.notional,
            )
        )
