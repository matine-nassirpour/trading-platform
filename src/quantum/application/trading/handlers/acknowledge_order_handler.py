from collections.abc import Sequence

from quantum.application.shared.base_handlers.aggregate_command_handler import (
    AggregateCommandHandler,
)
from quantum.application.shared.eventing.application_event_context import (
    ApplicationEventContext,
)
from quantum.application.trading.commands.acknowledge_order_command import (
    AcknowledgeOrderCommand,
)
from quantum.application.trading.results.order_command_result import (
    AcknowledgeOrderResult,
)
from quantum.domain.shared_kernel.event_sourcing.events.base_event import BaseEvent
from quantum.domain.trading.order.aggregate import Order, OrderId
from quantum.domain.trading.order.states.order_state_base import OrderStateBase


class AcknowledgeOrderHandler(
    AggregateCommandHandler[
        AcknowledgeOrderCommand,
        AcknowledgeOrderResult,
        OrderId,
        OrderStateBase,
        Order,
    ]
):
    """
    Use case: acknowledge a submitted order.

    Existence policy expected at composition root:
    - MUST_EXIST
    """

    def _aggregate_id(self, command: AcknowledgeOrderCommand) -> OrderId:
        return command.order_id

    def _context(self, command: AcknowledgeOrderCommand) -> ApplicationEventContext:
        return command.context

    def _execute_domain(
        self,
        *,
        command: AcknowledgeOrderCommand,
        aggregate: Order,
    ) -> tuple[Sequence[BaseEvent], AcknowledgeOrderResult]:
        events = aggregate.acknowledge()
        return events, AcknowledgeOrderResult(order_id=command.order_id)
