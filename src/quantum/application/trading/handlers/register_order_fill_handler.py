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
from quantum.domain.trading.common.value_objects.volume import NonNegativeVolume
from quantum.domain.trading.order.aggregate import Order, OrderId
from quantum.domain.trading.order.events.order_fill_registered_event import (
    OrderFillRegisteredEvent,
)
from quantum.domain.trading.order.states.order_initialized_state import (
    OrderInitializedState,
)
from quantum.domain.trading.order.states.order_state_base import OrderStateBase
from quantum.domain.trading.order.status.order_fill_status import OrderFillStatus
from quantum.domain.trading.order.status.order_lifecycle_status import (
    OrderLifecycleStatus,
)


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
        current_state = aggregate.state
        if not isinstance(current_state, OrderInitializedState):
            raise RuntimeError("Order must be initialized before fill registration")

        events = list(aggregate.register_fill(fill=command.fill))

        result = self._build_result(
            order_id=command.order_id,
            current_state=current_state,
            events=events,
        )

        return events, result

    @staticmethod
    def _build_result(
        *,
        order_id: OrderId,
        current_state: OrderInitializedState,
        events: Sequence[BaseEvent],
    ) -> RegisterOrderFillResult:
        if len(events) != 1:
            raise RuntimeError("Order.register_fill() must emit exactly one event")

        event = events[0]

        if not isinstance(event, OrderFillRegisteredEvent):
            raise RuntimeError(
                f"Unexpected fill registration event type: {type(event).__name__}"
            )

        new_filled_value = current_state.filled_volume.value + event.fill.volume.value

        if new_filled_value == current_state.requested_volume.value:
            fill_status = OrderFillStatus.filled()
            lifecycle_status = OrderLifecycleStatus.completed()
        else:
            fill_status = OrderFillStatus.partially_filled()
            lifecycle_status = current_state.lifecycle_status

        return RegisterOrderFillResult(
            order_id=order_id,
            filled_volume=NonNegativeVolume(new_filled_value),
            fill_status=fill_status,
            lifecycle_status=lifecycle_status,
        )
