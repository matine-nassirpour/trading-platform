from collections.abc import Sequence

from quantum.application.shared.base_handlers.aggregate_command_handler import (
    AggregateCommandHandler,
)
from quantum.application.shared.eventing.application_event_context import (
    ApplicationEventContext,
)
from quantum.application.trading.commands.cancel_order_command import CancelOrderCommand
from quantum.application.trading.results.order_command_result import CancelOrderResult
from quantum.domain.shared_kernel.event_sourcing.events.base_event import BaseEvent
from quantum.domain.trading.order.aggregate import Order, OrderId
from quantum.domain.trading.order.states.order_state_base import OrderStateBase


class CancelOrderHandler(
    AggregateCommandHandler[
        CancelOrderCommand,
        CancelOrderResult,
        OrderId,
        OrderStateBase,
        Order,
    ]
):
    """
    Use case: cancel an active order.

    Existence policy expected at composition root:
    - MUST_EXIST
    """

    def _aggregate_id(self, command: CancelOrderCommand) -> OrderId:
        return command.order_id

    def _context(self, command: CancelOrderCommand) -> ApplicationEventContext:
        return command.context

    async def _execute_domain(
        self,
        *,
        command: CancelOrderCommand,
        aggregate: Order,
    ) -> tuple[Sequence[BaseEvent], CancelOrderResult]:
        events = aggregate.cancel(
            cancelled_by=command.cancelled_by,
            reason=command.reason,
            origin=command.origin,
            cancelled_at=command.cancelled_at,
            comment=command.comment,
        )

        return events, CancelOrderResult(order_id=command.order_id)
