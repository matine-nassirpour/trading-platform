from collections.abc import Iterable

from quantum.application.shared.base_handlers.aggregate_command_handler import (
    AggregateCommandHandler,
)
from quantum.application.trading.commands.create_order_from_intent_command import (
    CreateOrderFromIntentCommand,
)
from quantum.domain.shared_kernel.events.base.base_event import BaseEvent
from quantum.domain.trading.execution.order.order import Order
from quantum.domain.trading.intent.trading_intent import TradingIntent


class CreateOrderFromIntentHandler(
    AggregateCommandHandler[CreateOrderFromIntentCommand, None, TradingIntent]
):
    """
    Creates an Order from an authorized TradingIntent.
    """

    def _stream_id(self, command: CreateOrderFromIntentCommand) -> str:
        return f"order-{command.intent_id.value}"

    def _execute_domain(
        self,
        *,
        command: CreateOrderFromIntentCommand,
        aggregate: TradingIntent,
    ) -> tuple[Iterable[BaseEvent], None]:

        domain_events = Order.create(
            intent_id=command.intent_id,
            order_id=command.order_id,
            symbol=command.symbol,
            order_type=command.order_type,
            side=command.side,
            volume=command.volume,
        )

        return domain_events, None
