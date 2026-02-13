from collections.abc import Iterable
from typing import Final

from quantum.application.commands.risk.register_pnl_command import RegisterPnLCommand
from quantum.application.handlers.event_sourced_command_handler import (
    EventSourcedCommandHandler,
)
from quantum.domain.risk.governance.aggregates.risk_state import RiskState
from quantum.domain.shared_kernel.events.base.base_event import BaseEvent


class RegisterPnLHandler(
    EventSourcedCommandHandler[RegisterPnLCommand, None, RiskState]
):
    """
    Registers realized PnL and updates global risk state.
    """

    _ACTOR: Final[str] = "system:risk_engine"

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
