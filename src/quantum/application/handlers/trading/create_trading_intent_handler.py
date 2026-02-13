from collections.abc import Iterable

from quantum.application.commands.trading.create_trading_intent_command import (
    CreateTradingIntentCommand,
)
from quantum.application.handlers.event_sourced_command_handler import (
    EventSourcedCommandHandler,
)
from quantum.domain.shared_kernel.events.base.base_event import BaseEvent
from quantum.domain.trading.intent.trading_intent import TradingIntent


class CreateTradingIntentHandler(
    EventSourcedCommandHandler[CreateTradingIntentCommand, None, None]
):
    """
    Creates a new TradingIntent aggregate.
    """

    def _stream_id(self, command: CreateTradingIntentCommand) -> str:
        return f"intent-{command.intent_id.value}"

    def _execute_domain(
        self,
        *,
        command: CreateTradingIntentCommand,
        aggregate,
    ) -> tuple[Iterable[BaseEvent], None]:

        domain_events = TradingIntent.create(
            intent_id=command.intent_id,
            symbol=command.symbol,
            side=command.side,
            decision_identity=command.decision_identity,
            context=command.context,
        )

        return domain_events, None
