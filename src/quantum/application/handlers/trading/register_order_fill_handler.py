from collections.abc import Iterable
from typing import Final

from quantum.application.commands.trading.register_order_fill_command import (
    RegisterOrderFillCommand,
)
from quantum.application.handlers.event_sourced_command_handler import (
    EventSourcedCommandHandler,
)
from quantum.application.ports.outbound.repositories.order_repository import (
    OrderRepository,
)
from quantum.domain.shared_kernel.events.base.base_event import BaseEvent
from quantum.domain.trading.execution.order.order import Order


class RegisterOrderFillHandler(
    EventSourcedCommandHandler[RegisterOrderFillCommand, None, Order]
):
    """
    Registers an execution fill on an existing Order aggregate.
    """

    _ACTOR: Final[str] = "system:execution"

    def __init__(
        self,
        *,
        order_repository: OrderRepository,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self._order_repository = order_repository

    def _stream_id(self, command: RegisterOrderFillCommand) -> str:
        return f"order-{command.order_id.value}"

    def _load_aggregate(self, command: RegisterOrderFillCommand) -> Order:
        return self._order_repository.load(command.order_id)

    def _execute_domain(
        self,
        *,
        command: RegisterOrderFillCommand,
        aggregate: Order,
    ) -> tuple[Iterable[BaseEvent], None]:

        domain_events = aggregate.register_fill(
            fill=command.fill,
        )

        return domain_events, None
