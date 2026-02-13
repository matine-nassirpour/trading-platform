from collections.abc import Iterable

from quantum.application.shared.base_handlers.aggregate_command_handler import (
    AggregateCommandHandler,
)
from quantum.application.trading.commands.register_order_fill_command import (
    RegisterOrderFillCommand,
)
from quantum.domain.shared_kernel.events.base.base_event import BaseEvent
from quantum.domain.trading.execution.order.order import Order


class RegisterOrderFillHandler(
    AggregateCommandHandler[RegisterOrderFillCommand, None, Order]
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
