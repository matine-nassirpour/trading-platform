from collections.abc import Iterable

from quantum.application.shared.base_handlers.aggregate_command_handler import (
    AggregateCommandHandler,
)
from quantum.application.shared.base_handlers.aggregate_existence_policy import (
    AggregateExistencePolicy,
)
from quantum.application.trading.commands.create_order_from_intent_command import (
    CreateOrderFromIntentCommand,
)
from quantum.domain.shared_kernel.events.base.base_event import BaseEvent
from quantum.domain.trading.execution.order.order import Order


class CreateOrderFromIntentHandler(
    AggregateCommandHandler[CreateOrderFromIntentCommand, None, Order]
):
    """
    Creates an Order from an authorized TradingIntent.
    """

    def __init__(self, **kwargs) -> None:
        super().__init__(
            existence_policy=AggregateExistencePolicy.MUST_NOT_EXIST,
            **kwargs,
        )

    def _stream_id(self, command: CreateOrderFromIntentCommand) -> str:
        return f"order-{command.intent_id.value}"

    def _execute_domain(
        self,
        *,
        command: CreateOrderFromIntentCommand,
        aggregate: Order | None,
    ) -> tuple[Iterable[BaseEvent], None]:

        if aggregate is not None:
            raise RuntimeError(
                "Order aggregate already exists "
                "despite MUST_NOT_EXIST policy enforcement."
            )

        domain_events = Order.create(
            intent_id=command.intent_id,
            broker_order_id=command.broker_order_id,
            symbol=command.symbol,
            order_type=command.order_type,
            side=command.side,
            volume=command.volume,
        )

        return domain_events, None
