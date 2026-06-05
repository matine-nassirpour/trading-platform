from collections.abc import Sequence

from quantum.application.shared.base_handlers.aggregate_command_handler import (
    AggregateCommandHandler,
)
from quantum.application.shared.eventing.application_event_context import (
    ApplicationEventContext,
)
from quantum.application.trading.commands.accept_order_command import AcceptOrderCommand
from quantum.application.trading.results.order_command_result import AcceptOrderResult
from quantum.domain.shared_kernel.event_sourcing.events.base_event import BaseEvent
from quantum.domain.trading.order.aggregate import Order, OrderId
from quantum.domain.trading.order.states.order_state_base import OrderStateBase


class AcceptOrderHandler(
    AggregateCommandHandler[
        AcceptOrderCommand,
        AcceptOrderResult,
        OrderId,
        OrderStateBase,
        Order,
    ]
):
    """
    Use case: accept an acknowledged order.

    Existence policy expected at composition root:
    - MUST_EXIST
    """

    def _aggregate_id(self, command: AcceptOrderCommand) -> OrderId:
        return command.order_id

    def _context(self, command: AcceptOrderCommand) -> ApplicationEventContext:
        return command.context

    async def _execute_domain(
        self,
        *,
        command: AcceptOrderCommand,
        aggregate: Order,
    ) -> tuple[Sequence[BaseEvent], AcceptOrderResult]:
        events = aggregate.accept()
        return events, AcceptOrderResult(order_id=command.order_id)
