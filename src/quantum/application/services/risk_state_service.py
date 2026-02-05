from quantum.application.ports.outbound.event_store import EventStore
from quantum.application.ports.outbound.risk_state_repository import RiskStateRepository
from quantum.domain.shared_kernel.money.daily_loss import DailyLoss
from quantum.domain.shared_kernel.money.drawdown import Drawdown
from quantum.domain.shared_kernel.money.notional import Notional
from quantum.domain.shared_kernel.money.risk_exposure import RiskExposure
from quantum.domain.shared_kernel.value_objects.pnl import RealizedPnL


class RiskStateService:

    def __init__(
        self,
        repository: RiskStateRepository,
        event_store: EventStore,
    ) -> None:
        self._repository = repository
        self._event_store = event_store

    def register_pnl(
        self,
        *,
        pnl: RealizedPnL,
        drawdown: Drawdown,
        daily_loss: DailyLoss,
        exposure: RiskExposure,
        notional: Notional,
    ) -> None:

        aggregate = self._repository.load()

        events = aggregate.register_pnl(
            pnl=pnl,
            drawdown=drawdown,
            daily_loss=daily_loss,
            exposure=exposure,
            notional=notional,
        )

        self._event_store.append(events)
