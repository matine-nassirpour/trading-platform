from collections.abc import Sequence

from quantum.application.shared.base_handlers.aggregate_command_handler import (
    AggregateCommandHandler,
)
from quantum.application.shared.eventing.application_event_context import (
    ApplicationEventContext,
)
from quantum.application.trading.commands.register_order_fill_command import (
    RegisterOrderFillCommand,
)
from quantum.application.trading.results.order_command_result import (
    RegisterOrderFillResult,
)
from quantum.domain.shared_kernel.event_sourcing.events.base_event import BaseEvent
from quantum.domain.trading.order.aggregate import Order, OrderId
from quantum.domain.trading.order.states.order_state_base import OrderStateBase


class RegisterOrderFillHandler(
    AggregateCommandHandler[
        RegisterOrderFillCommand,
        RegisterOrderFillResult,
        OrderId,
        OrderStateBase,
        Order,
    ]
):
    """
    Use case: register an execution fill against an accepted order.

    Existence policy expected at composition root:
    - MUST_EXIST
    """

    def _aggregate_id(self, command: RegisterOrderFillCommand) -> OrderId:
        return command.order_id

    def _context(self, command: RegisterOrderFillCommand) -> ApplicationEventContext:
        return command.context

    def _execute_domain(
        self,
        *,
        command: RegisterOrderFillCommand,
        aggregate: Order,
    ) -> tuple[Sequence[BaseEvent], RegisterOrderFillResult]:
        outcome, events = aggregate.register_fill(fill=command.fill)

        return events, RegisterOrderFillResult(
            order_id=command.order_id,
            filled_volume=outcome.filled_volume,
            fill_status=outcome.fill_status,
            lifecycle_status=outcome.lifecycle_status,
        )
