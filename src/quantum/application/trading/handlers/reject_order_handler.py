from collections.abc import Sequence

from quantum.application.shared.base_handlers.aggregate_command_handler import (
    AggregateCommandHandler,
)
from quantum.application.shared.eventing.application_event_context import (
    ApplicationEventContext,
)
from quantum.application.trading.commands.reject_order_command import RejectOrderCommand
from quantum.application.trading.results.order_command_result import RejectOrderResult
from quantum.domain.shared_kernel.event_sourcing.events.base_event import BaseEvent
from quantum.domain.trading.order.aggregate import Order, OrderId
from quantum.domain.trading.order.states.order_state_base import OrderStateBase


class RejectOrderHandler(
    AggregateCommandHandler[
        RejectOrderCommand,
        RejectOrderResult,
        OrderId,
        OrderStateBase,
        Order,
    ]
):
    """
    Use case: reject an active order.

    Existence policy expected at composition root:
    - MUST_EXIST
    """

    def _aggregate_id(self, command: RejectOrderCommand) -> OrderId:
        return command.order_id

    def _context(self, command: RejectOrderCommand) -> ApplicationEventContext:
        return command.context

    async def _execute_domain(
        self,
        *,
        command: RejectOrderCommand,
        aggregate: Order,
    ) -> tuple[Sequence[BaseEvent], RejectOrderResult]:
        events = aggregate.reject(rejection=command.rejection)
        return events, RejectOrderResult(order_id=command.order_id)
