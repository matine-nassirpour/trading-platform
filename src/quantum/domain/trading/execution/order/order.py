from collections.abc import Mapping
from dataclasses import dataclass

from quantum.domain.shared_kernel.errors.invariants import (
    InvalidStateTransition,
    InvariantViolation,
)
from quantum.domain.shared_kernel.errors.order_errors import (
    OrderNotFillable,
    OrderOverfill,
)
from quantum.domain.shared_kernel.events.base.base_event import BaseEvent
from quantum.domain.shared_kernel.events.event_sequence import EventSequence
from quantum.domain.shared_kernel.events.persisted_event_envelope import (
    PersistedEventEnvelope,
)
from quantum.domain.shared_kernel.identifiers.aggregate_id import AggregateId
from quantum.domain.shared_kernel.identifiers.broker_order_id import BrokerOrderId
from quantum.domain.shared_kernel.identifiers.intent_id import IntentId
from quantum.domain.shared_kernel.primitives.event_sourced_aggregate_root import (
    EventHandler,
    EventSourcedAggregateRoot,
)
from quantum.domain.shared_kernel.value_objects.symbol import Symbol
from quantum.domain.shared_kernel.value_objects.volume import (
    NonNegativeVolume,
    PositiveVolume,
)
from quantum.domain.trading.events.v1.order.order_cancelled_event import (
    OrderCancelledEvent,
)
from quantum.domain.trading.events.v1.order.order_created_event import OrderCreatedEvent
from quantum.domain.trading.events.v1.order.order_fill_registered_event import (
    OrderFillRegisteredEvent,
)
from quantum.domain.trading.execution.order.execution_fill import ExecutionFill
from quantum.domain.trading.execution.order.order_initialized_state import (
    OrderInitializedState,
)
from quantum.domain.trading.execution.order.order_state_base import OrderStateBase
from quantum.domain.trading.execution.order.order_status import OrderStatus
from quantum.domain.trading.execution.order.order_type import OrderType
from quantum.domain.trading.execution.order.order_uninitialized_state import (
    OrderUninitializedState,
)
from quantum.domain.trading.execution.order.position_side import PositionSide


@dataclass(frozen=True, slots=True)
class OrderId(AggregateId):
    """Identity of the Order aggregate (event stream id)."""

    pass


class Order(EventSourcedAggregateRoot[OrderId, OrderStateBase]):
    """
    Event-sourced Order aggregate.

    Institutional guarantees:

    - No implicit state
    - Explicit initialization lifecycle
    - Deterministic replay
    - Strict invariant enforcement
    - Immutable aggregate
    """

    __slots__ = ()

    @classmethod
    def empty_state(cls) -> OrderStateBase:
        return OrderUninitializedState(
            last_sequence=EventSequence.initial(),
        )

    # --- Factory --------------------------------------------------------------

    def create(
        self,
        *,
        intent_id: IntentId,
        broker_order_id: BrokerOrderId,
        symbol: Symbol,
        order_type: OrderType,
        side: PositionSide,
        volume: PositiveVolume,
    ) -> list[BaseEvent]:
        """
        Create a new Order aggregate.

        This method represents the domain-level decision to expose capital
        by creating an order with a specific intent, side and volume.
        """

        if not isinstance(self.state, OrderUninitializedState):
            raise InvalidStateTransition("Order creation requires uninitialized state")

        return [
            OrderCreatedEvent(
                intent_id=intent_id,
                broker_order_id=broker_order_id,
                symbol=symbol,
                order_type=order_type,
                side=side,
                volume=volume,
            )
        ]

    # --- Commands -------------------------------------------------------------

    def register_fill(self, *, fill: ExecutionFill) -> list[BaseEvent]:
        """
        Registers an execution fill against this order.

        This method represents the domain acknowledgment that
        a portion (or the entirety) of the order has been executed.
        """

        state = self.state

        if not isinstance(state, OrderInitializedState):
            raise InvalidStateTransition("Cannot fill uninitialized order")

        if not state.status.is_fillable():
            raise OrderNotFillable("Order is not in a fillable state")

        new_total = state.filled_volume.value + fill.volume.value

        if new_total > state.requested_volume.value:
            raise OrderOverfill("Fill exceeds remaining order volume")

        return [
            OrderFillRegisteredEvent(
                broker_order_id=state.broker_order_id,
                fill=fill,
            )
        ]

    def cancel(self) -> list[BaseEvent]:
        """
        Cancels the order if it has not yet reached a terminal state.

        Semantics:
        - Cancellation is a domain decision
        - A cancelled order cannot be filled afterwards
        - Partial fills remain valid and preserved
        """

        state = self.state

        if not isinstance(state, OrderInitializedState):
            raise InvalidStateTransition("Cannot cancel uninitialized order")

        if state.status.is_terminal():
            raise OrderNotFillable("Order already terminal")

        return [
            OrderCancelledEvent(
                broker_order_id=state.broker_order_id,
            )
        ]

    # --- Event → State transitions --------------------------------------------

    @staticmethod
    def _apply_created(
        state: OrderStateBase,
        event: BaseEvent,
        envelope: PersistedEventEnvelope,
    ) -> OrderStateBase:
        """
        Answers the question:
            "Given that an order creation event occurred,
             what is the resulting aggregate state?"

        This method represents a PURE EVENT → STATE TRANSITION.
        """

        if not isinstance(state, OrderUninitializedState):
            raise InvariantViolation("Order already created")

        if not isinstance(event, OrderCreatedEvent):
            raise InvariantViolation("Invalid event type")

        return OrderInitializedState(
            last_sequence=envelope.sequence,
            broker_order_id=event.broker_order_id,
            symbol=event.symbol,
            order_type=event.order_type,
            side=event.side,
            requested_volume=event.volume,
            filled_volume=NonNegativeVolume.zero(),
            status=OrderStatus.pending(),
        )

    @staticmethod
    def _apply_fill_registered(
        state: OrderStateBase,
        event: BaseEvent,
        envelope: PersistedEventEnvelope,
    ) -> OrderStateBase:
        """
        Answers the question:
            "Given that a fill occurred, how does it affect the order state?"

        This method represents a PURE EVENT → STATE TRANSITION.
        """

        if not isinstance(state, OrderInitializedState):
            raise InvariantViolation("Order not initialized")

        if not isinstance(event, OrderFillRegisteredEvent):
            raise InvariantViolation("Invalid event type")

        if event.broker_order_id != state.broker_order_id:
            raise InvariantViolation("Illegal fill event: broker_order_id mismatch")

        # Industry-grade ES rule: handlers must also enforce replay integrity.
        if not state.status.is_fillable():
            raise InvariantViolation("Illegal fill event: order is not fillable")

        new_filled = state.filled_volume.value + event.fill.volume.value

        if new_filled > state.requested_volume.value:
            raise InvariantViolation("Illegal fill event: overfill")

        new_status = (
            OrderStatus.filled()
            if new_filled == state.requested_volume.value
            else OrderStatus.partially_filled()
        )

        return OrderInitializedState(
            last_sequence=envelope.sequence,
            broker_order_id=state.broker_order_id,
            symbol=state.symbol,
            order_type=state.order_type,
            side=state.side,
            requested_volume=state.requested_volume,
            filled_volume=NonNegativeVolume(new_filled),
            status=new_status,
        )

    @staticmethod
    def _apply_cancelled(
        state: OrderStateBase,
        event: BaseEvent,
        envelope: PersistedEventEnvelope,
    ) -> OrderStateBase:
        """
        Answers the question:
            "Given that the order was cancelled,
             what is the resulting aggregate state?"

        This method represents a PURE EVENT → STATE TRANSITION.
        """

        if not isinstance(state, OrderInitializedState):
            raise InvariantViolation("Order not initialized")

        if not isinstance(event, OrderCancelledEvent):
            raise InvariantViolation("Invalid event type")

        if event.broker_order_id != state.broker_order_id:
            raise InvariantViolation("Illegal cancel event: broker_order_id mismatch")

        if state.status.is_terminal():
            raise InvariantViolation("Illegal cancel event: order already terminal")

        return OrderInitializedState(
            last_sequence=envelope.sequence,
            broker_order_id=state.broker_order_id,
            symbol=state.symbol,
            order_type=state.order_type,
            side=state.side,
            requested_volume=state.requested_volume,
            filled_volume=state.filled_volume,
            status=OrderStatus.cancelled(),
        )

    @classmethod
    def _handlers(
        cls,
    ) -> Mapping[type[BaseEvent], EventHandler[OrderStateBase, BaseEvent]]:
        return {
            OrderCreatedEvent: cls._apply_created,
            OrderFillRegisteredEvent: cls._apply_fill_registered,
            OrderCancelledEvent: cls._apply_cancelled,
        }
