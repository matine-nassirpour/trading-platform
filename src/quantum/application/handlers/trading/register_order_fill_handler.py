from collections.abc import Iterable

from quantum.application.commands.trading.register_order_fill_command import (
    RegisterOrderFillCommand,
)
from quantum.application.handlers.event_sourced_command_handler import (
    EventSourcedCommandHandler,
)
from quantum.domain.shared_kernel.events.base.base_event import BaseEvent
from quantum.domain.trading.execution.order.order import Order


class RegisterOrderFillHandler(
    EventSourcedCommandHandler[RegisterOrderFillCommand, None, Order]
):
    """
    Registers an execution fill on an existing Order aggregate.
    """

    def _stream_id(self, command: RegisterOrderFillCommand) -> str:
        return f"order-{command.order_id.value}"

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
