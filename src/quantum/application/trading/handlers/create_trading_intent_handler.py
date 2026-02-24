from collections.abc import Iterable

from quantum.application.shared.base_handlers.aggregate_command_handler import (
    AggregateCommandHandler,
)
from quantum.application.shared.base_handlers.aggregate_existence_policy import (
    AggregateExistencePolicy,
)
from quantum.application.trading.commands.create_trading_intent_command import (
    CreateTradingIntentCommand,
)
from quantum.domain.shared_kernel.events.base.base_event import BaseEvent
from quantum.domain.trading.intent.trading_intent import TradingIntent


class CreateTradingIntentHandler(
    AggregateCommandHandler[CreateTradingIntentCommand, None, TradingIntent]
):
    """
    Creates a new TradingIntent aggregate.
    """

    def __init__(self, **kwargs) -> None:
        super().__init__(
            existence_policy=AggregateExistencePolicy.MUST_NOT_EXIST, **kwargs
        )

    def _stream_id(self, command: CreateTradingIntentCommand) -> str:
        return f"intent-{command.intent_id.value}"

    def _execute_domain(
        self,
        *,
        command: CreateTradingIntentCommand,
        aggregate: TradingIntent,
    ) -> tuple[Iterable[BaseEvent], None]:

        domain_events = TradingIntent.create(
            intent_id=command.intent_id,
            symbol=command.symbol,
            side=command.side,
            decision_identity=command.decision_identity,
            context=command.context,
        )

        return domain_events, None
