from collections.abc import Iterable

from quantum.application.risk.commands.register_pnl_command import RegisterPnLCommand
from quantum.application.shared.base_handlers.aggregate_command_handler import (
    AggregateCommandHandler,
)
from quantum.application.shared.base_handlers.aggregate_existence_policy import (
    AggregateExistencePolicy,
)
from quantum.domain.risk.governance.aggregates.risk_state import RiskState
from quantum.domain.shared_kernel.events.base.base_event import BaseEvent


class RegisterPnLHandler(AggregateCommandHandler[RegisterPnLCommand, None, RiskState]):
    """
    Registers realized PnL and updates global risk state.
    """

    def __init__(self, **kwargs) -> None:
        super().__init__(
            existence_policy=AggregateExistencePolicy.MUST_EXIST,
            **kwargs,
        )

    def _stream_id(self, command: RegisterPnLCommand) -> str:
        return "risk-state"

    def _execute_domain(
        self,
        *,
        command: RegisterPnLCommand,
        aggregate: RiskState,
    ) -> tuple[Iterable[BaseEvent], None]:

        domain_events = aggregate.register_pnl(
            pnl=command.pnl,
            drawdown=command.drawdown,
            daily_loss=command.daily_loss,
            exposure=command.exposure,
            notional=command.notional,
        )

        return domain_events, None
