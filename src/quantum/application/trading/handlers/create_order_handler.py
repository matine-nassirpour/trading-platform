from collections.abc import Sequence

from quantum.application.shared.base_handlers.aggregate_command_handler import (
    AggregateCommandHandler,
)
from quantum.application.shared.eventing.application_event_context import (
    ApplicationEventContext,
)
from quantum.application.trading.commands.create_order_command import CreateOrderCommand
from quantum.application.trading.results.order_command_result import CreateOrderResult
from quantum.domain.shared_kernel.event_sourcing.events.base_event import BaseEvent
from quantum.domain.trading.order.aggregate import Order, OrderId
from quantum.domain.trading.order.states.order_state_base import OrderStateBase


class CreateOrderHandler(
    AggregateCommandHandler[
        CreateOrderCommand,
        CreateOrderResult,
        OrderId,
        OrderStateBase,
        Order,
    ]
):
    """
    Use case: create a new Order aggregate.

    Existence policy expected at composition root:
    - MUST_NOT_EXIST
    """

    def _aggregate_id(self, command: CreateOrderCommand) -> OrderId:
        return command.order_id

    def _context(self, command: CreateOrderCommand) -> ApplicationEventContext:
        return command.context

    async def _execute_domain(
        self,
        *,
        command: CreateOrderCommand,
        aggregate: Order,
    ) -> tuple[Sequence[BaseEvent], CreateOrderResult]:
        _, events = Order.create_new(
            aggregate_id=command.order_id,
            decision_id=command.decision_id,
            broker_order_ref=command.broker_order_ref,
            symbol=command.symbol,
            order_kind=command.order_kind,
            side=command.side,
            volume=command.volume,
            reference_price=command.reference_price,
            stop_price=command.stop_price,
            limit_price=command.limit_price,
            sl=command.sl,
            tp=command.tp,
            time_in_force=command.time_in_force,
        )

        return events, CreateOrderResult(order_id=command.order_id)
