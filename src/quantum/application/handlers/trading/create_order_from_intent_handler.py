from collections.abc import Iterable
from typing import Final

from quantum.application.commands.trading.create_order_from_intent_command import (
    CreateOrderFromIntentCommand,
)
from quantum.application.errors.application_error import UseCaseError
from quantum.application.handlers.event_sourced_command_handler import (
    EventSourcedCommandHandler,
)
from quantum.application.ports.outbound.repositories.trading_intent_repository import (
    TradingIntentRepository,
)
from quantum.domain.shared_kernel.events.base.base_event import BaseEvent
from quantum.domain.trading.execution.order.order import Order
from quantum.domain.trading.intent.trading_intent import TradingIntent


class CreateOrderFromIntentHandler(
    EventSourcedCommandHandler[CreateOrderFromIntentCommand, None, TradingIntent]
):
    """
    Creates an Order from an authorized TradingIntent.
    """

    _ACTOR: Final[str] = "system:order"

    def __init__(
        self,
        *,
        repository: TradingIntentRepository,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self._repository = repository

    def _stream_id(self, command: CreateOrderFromIntentCommand) -> str:
        return f"order-{command.order_id.value}"

    def _load_aggregate(self, command: CreateOrderFromIntentCommand) -> TradingIntent:
        return self._repository.load(command.intent_id)

    def _execute_domain(
        self,
        *,
        command: CreateOrderFromIntentCommand,
        aggregate: TradingIntent,
    ) -> tuple[Iterable[BaseEvent], None]:

        if not aggregate.state.authorized:
            raise UseCaseError("Cannot create order from non-authorized intent")

        domain_events = Order.create(
            intent_id=command.intent_id,
            order_id=command.order_id,
            symbol=command.symbol,
            order_type=command.order_type,
            side=command.side,
            volume=command.volume,
        )

        return domain_events, None
