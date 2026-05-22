from collections.abc import Iterable

from quantum.application.shared.base_handlers.aggregate_command_handler import (
    AggregateCommandHandler,
)
from quantum.application.shared.base_handlers.aggregate_existence_policy import (
    AggregateExistencePolicy,
)
from quantum.application.trading.commands.register_order_fill_command import (
    RegisterOrderFillCommand,
)
from quantum.domain.shared_kernel.event_sourcing.events.base_event import BaseEvent
from quantum.domain.trading.order.aggregate import Order


class RegisterOrderFillHandler(
    AggregateCommandHandler[RegisterOrderFillCommand, None, Order]
):
    """
    Registers an execution fill on an existing Order aggregate.
    """

    def __init__(self, **kwargs) -> None:
        super().__init__(
            existence_policy=AggregateExistencePolicy.MUST_EXIST,
            **kwargs,
        )

    def _stream_id(self, command: RegisterOrderFillCommand) -> str:
        return f"order-{command.broker_order_id.value}"

    def _execute_domain(
        self,
        *,
        command: RegisterOrderFillCommand,
        aggregate: Order | None,
    ) -> tuple[Iterable[BaseEvent], None]:

        if aggregate is None:
            raise RuntimeError(
                "Order aggregate missing despite MUST_EXIST policy enforcement."
            )

        domain_events = aggregate.register_fill(
            fill=command.fill,
        )

        return domain_events, None
