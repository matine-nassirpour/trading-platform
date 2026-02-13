from collections.abc import Iterable

from quantum.application.commands.decision.register_no_trade_command import (
    RegisterNoTradeCommand,
)
from quantum.application.handlers.event_sourced_command_handler import (
    EventSourcedCommandHandler,
)
from quantum.domain.decision.events.v1.no_trade_decision_event import (
    NoTradeDecisionEvent,
)
from quantum.domain.shared_kernel.events.base.base_event import BaseEvent


class RegisterNoTradeHandler(
    EventSourcedCommandHandler[RegisterNoTradeCommand, None, None]
):
    """
    Registers a No-Trade decision in a strictly transactional,
    event-sourced and concurrency-safe manner.
    """

    def _stream_id(self, command: RegisterNoTradeCommand) -> str:
        return f"decision-{command.decision_identity.strategy_id.value}"

    def _execute_domain(
        self,
        *,
        command: RegisterNoTradeCommand,
        aggregate,
    ) -> tuple[Iterable[BaseEvent], None]:

        events = [
            NoTradeDecisionEvent(
                symbol=command.symbol,
                decision_identity=command.decision_identity,
                no_trade_decision=command.outcome,
            )
        ]

        return events, None
