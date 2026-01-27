from collections.abc import Mapping
from dataclasses import dataclass

from quantum.domain.shared_kernel.errors.invariants import InvariantViolation
from quantum.domain.shared_kernel.errors.order_errors import (
    OrderNotFillable,
    OrderOverfill,
)
from quantum.domain.shared_kernel.events.base_event import BaseEvent
from quantum.domain.shared_kernel.events.event_envelope import EventEnvelope
from quantum.domain.shared_kernel.events.event_sequence import EventSequence
from quantum.domain.shared_kernel.identifiers.intent_id import IntentId
from quantum.domain.shared_kernel.identifiers.order_id import OrderId
from quantum.domain.shared_kernel.primitives.aggregate_state import AggregateState
from quantum.domain.shared_kernel.primitives.event_sourced_aggregate_root import (
    EventHandler,
    EventSourcedAggregateRoot,
)
from quantum.domain.shared_kernel.value_objects.symbol import Symbol
from quantum.domain.shared_kernel.value_objects.volume import (
    NonNegativeVolume,
    PositiveVolume,
)
from quantum.domain.trading.events.v1.execution.order_cancelled_event import (
    OrderCancelledEvent,
)
from quantum.domain.trading.events.v1.execution.order_created_event import (
    OrderCreatedEvent,
)
from quantum.domain.trading.events.v1.execution.order_fill_registered_event import (
    OrderFillRegisteredEvent,
)
from quantum.domain.trading.execution.order.execution_fill import ExecutionFill
from quantum.domain.trading.execution.order.order_status import OrderStatus
from quantum.domain.trading.execution.order.order_type import OrderType
from quantum.domain.trading.execution.order.position_side import PositionSide


@dataclass(frozen=True, slots=True)
class OrderState(AggregateState):
    last_sequence: EventSequence

    order_id: OrderId
    symbol: Symbol

    order_type: OrderType
    side: PositionSide

    requested_volume: PositiveVolume
    filled_volume: NonNegativeVolume

    status: OrderStatus

    def last_event_sequence(self) -> EventSequence:
        return self.last_sequence

    # --- Aggregate invariants -------------------------------------------------

    def _validate_identity(self) -> None:
        if not isinstance(self.order_id, OrderId):
            raise InvariantViolation("OrderId is required")

        if not isinstance(self.symbol, Symbol):
            raise InvariantViolation("Order must be bound to a Symbol")

        if not isinstance(self.order_type, OrderType):
            raise InvariantViolation("OrderType is required")

        if not isinstance(self.side, PositionSide):
            raise InvariantViolation("PositionSide is required")

    def _validate_volume(self) -> None:
        if not isinstance(self.requested_volume, PositiveVolume):
            raise InvariantViolation("Requested volume is required")

        if not isinstance(self.filled_volume, NonNegativeVolume):
            raise InvariantViolation("Filled volume is required")

        if self.filled_volume.value > self.requested_volume.value:
            raise InvariantViolation("Order cannot be overfilled")

    def _assert_status_consistency(self) -> None:
        if not isinstance(self.status, OrderStatus):
            raise InvariantViolation("OrderStatus is required")

        if (
            self.status.is_filled()
            and self.filled_volume.value != self.requested_volume.value
        ):
            raise InvariantViolation("Filled order must be fully filled")

        if (
            self.status.is_cancelled()
            and self.filled_volume.value == self.requested_volume.value
        ):
            raise InvariantViolation("Cancelled order cannot be fully filled")

    def _validate(self) -> None:
        self._validate_identity()
        self._validate_volume()
        self._assert_status_consistency()


class Order(EventSourcedAggregateRoot[OrderState]):
    """
    Event-sourced Order aggregate.

    Responsibilities:
    - enforce order lifecycle
    - track fills
    - guarantee volume & status consistency
    """

    # --- Factory --------------------------------------------------------------

    @staticmethod
    def create(
        *,
        intent_id: IntentId,
        order_id: OrderId,
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

        return [
            OrderCreatedEvent(
                intent_id=intent_id,
                order_id=order_id,
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

        if not state.status.is_fillable():
            raise OrderNotFillable("Order is not in a fillable state")

        if state.filled_volume.value + fill.volume.value > state.requested_volume.value:
            raise OrderOverfill("Fill exceeds remaining order volume")

        return [
            OrderFillRegisteredEvent(
                order_id=state.order_id,
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
        if state.status.is_terminal():
            raise OrderNotFillable("Order already terminal")

        return [
            OrderCancelledEvent(
                order_id=state.order_id,
            )
        ]

    # --- Event → State transitions --------------------------------------------

    @staticmethod
    def _apply_created(
        state: OrderState | None,
        event: BaseEvent,
        envelope: EventEnvelope,
    ) -> OrderState:
        """
        Answers the question:
            "Given that an order creation event occurred,
             what is the resulting aggregate state?"

        This method represents a PURE EVENT → STATE TRANSITION.
        """

        if state is not None:
            raise InvariantViolation("Order already exists")

        assert isinstance(event, OrderCreatedEvent)

        return OrderState(
            last_sequence=envelope.sequence,
            order_id=event.order_id,
            symbol=event.symbol,
            order_type=event.order_type,
            side=event.side,
            requested_volume=event.volume,
            filled_volume=NonNegativeVolume.zero(),
            status=OrderStatus.pending(),
        )

    @staticmethod
    def _apply_fill_registered(
        state: OrderState,
        event: BaseEvent,
        envelope: EventEnvelope,
    ) -> OrderState:
        """
        Answers the question:
            "Given that a fill occurred, how does it affect the order state?"

        This method represents a PURE EVENT → STATE TRANSITION.
        """

        assert isinstance(event, OrderFillRegisteredEvent)

        new_filled = state.filled_volume.value + event.fill.volume.value

        new_status = (
            OrderStatus.filled()
            if new_filled == state.requested_volume.value
            else OrderStatus.partially_filled()
        )

        return OrderState(
            last_sequence=envelope.sequence,
            order_id=state.order_id,
            symbol=state.symbol,
            order_type=state.order_type,
            side=state.side,
            requested_volume=state.requested_volume,
            filled_volume=NonNegativeVolume(new_filled),
            status=new_status,
        )

    @staticmethod
    def _apply_cancelled(
        state: OrderState,
        event: BaseEvent,
        envelope: EventEnvelope,
    ) -> OrderState:
        """
        Answers the question:
            "Given that the order was cancelled,
             what is the resulting aggregate state?"

        This method represents a PURE EVENT → STATE TRANSITION.
        """

        assert isinstance(event, OrderCancelledEvent)

        return OrderState(
            last_sequence=envelope.sequence,
            order_id=state.order_id,
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
    ) -> Mapping[type[BaseEvent], EventHandler[OrderState, BaseEvent]]:
        return {
            OrderCreatedEvent: cls._apply_created,
            OrderFillRegisteredEvent: cls._apply_fill_registered,
            OrderCancelledEvent: cls._apply_cancelled,
        }
