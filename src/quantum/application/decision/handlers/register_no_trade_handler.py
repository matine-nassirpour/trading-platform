from collections.abc import Iterable

from quantum.application.decision.commands.register_no_trade_command import (
    RegisterNoTradeCommand,
)
from quantum.application.shared.base_handlers.process_command_handler import (
    ProcessCommandHandler,
)
from quantum.domain.decision.no_trade.no_trade_decision_event import (
    NoTradeDecisionEvent,
)
from quantum.domain.shared_kernel.event_sourcing.events.base_event import BaseEvent


class RegisterNoTradeHandler(ProcessCommandHandler[RegisterNoTradeCommand, None]):
    """
    Registers a No-Trade decision in a strictly transactional,
    event-sourced and concurrency-safe manner.
    """

    def _execute_domain(
        self,
        *,
        command: RegisterNoTradeCommand,
    ) -> tuple[Iterable[BaseEvent], None]:

        events = [
            NoTradeDecisionEvent(
                symbol=command.symbol,
                decision_identity=command.decision_identity,
                no_trade_decision=command.outcome,
            )
        ]

        return events, None
