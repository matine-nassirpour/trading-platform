from collections.abc import Mapping
from dataclasses import dataclass
from typing import Self

from quantum.domain.market.instrument.identity.symbol import Symbol
from quantum.domain.market.instrument.pricing.reference_price import ReferencePrice
from quantum.domain.shared_kernel.event_sourcing.aggregates.event_sourced_aggregate_root import (
    EventHandler,
    EventSourcedAggregateRoot,
)
from quantum.domain.shared_kernel.event_sourcing.events.base_event import BaseEvent
from quantum.domain.shared_kernel.event_sourcing.events.event_sequence import (
    EventSequence,
)
from quantum.domain.shared_kernel.event_sourcing.events.recorded_event_envelope import (
    RecordedEventEnvelope,
)
from quantum.domain.shared_kernel.foundation.errors.invariants import (
    InvalidStateTransition,
    InvariantViolation,
)
from quantum.domain.shared_kernel.modeling.identity.aggregate_id import AggregateId
from quantum.domain.shared_kernel.modeling.identity.decision_id import DecisionId
from quantum.domain.shared_kernel.modeling.monetary.price import Price
from quantum.domain.trading.common.errors.order_errors import (
    OrderNotFillable,
    OrderOverfill,
)
from quantum.domain.trading.common.value_objects.position_side import PositionSide
from quantum.domain.trading.common.value_objects.volume import (
    NonNegativeVolume,
    PositiveVolume,
)
from quantum.domain.trading.execution.fills.execution_fill import ExecutionFill
from quantum.domain.trading.identity.broker_order_ref import BrokerOrderRef
from quantum.domain.trading.order.events.order_cancelled_event import (
    OrderCancelledEvent,
)
from quantum.domain.trading.order.events.order_created_event import OrderCreatedEvent
from quantum.domain.trading.order.events.order_fill_registered_event import (
    OrderFillRegisteredEvent,
)
from quantum.domain.trading.order.order_kind import OrderKind
from quantum.domain.trading.order.order_status import OrderStatus
from quantum.domain.trading.order.states.order_initialized_state import (
    OrderInitializedState,
)
from quantum.domain.trading.order.states.order_state_base import OrderStateBase
from quantum.domain.trading.order.states.order_uninitialized_state import (
    OrderUninitializedState,
)
from quantum.domain.trading.order.time_in_force import TimeInForce


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
    def aggregate_id_type(cls) -> type[OrderId]:
        return OrderId

    @classmethod
    def state_type(cls) -> type[OrderStateBase]:
        return OrderStateBase

    @classmethod
    def uninitialized_state(cls) -> OrderStateBase:
        return OrderUninitializedState(
            last_sequence=EventSequence.initial(),
        )

    # --- Creation API ---------------------------------------------------------

    @classmethod
    def decide_create(
        cls,
        *,
        intent_id: DecisionId,
        broker_order_ref: BrokerOrderRef,
        symbol: Symbol,
        order_kind: OrderKind,
        side: PositionSide,
        volume: PositiveVolume,
        reference_price: ReferencePrice | None = None,
        stop_price: Price | None = None,
        limit_price: Price | None = None,
        sl: Price | None = None,
        tp: Price | None = None,
        time_in_force: TimeInForce | None = None,
    ) -> list[BaseEvent]:
        """
        Pure domain decision for aggregate creation.

        This method does NOT require an aggregate instance.
        It only answers the business question:
            "Which event(s) must exist for a new Order to be created?"

        Returns NEW domain events, not recorded envelopes.
        """

        return [
            OrderCreatedEvent(
                intent_id=intent_id,
                broker_order_ref=broker_order_ref,
                symbol=symbol,
                order_kind=order_kind,
                side=side,
                volume=volume,
                reference_price=reference_price,
                stop_price=stop_price,
                limit_price=limit_price,
                sl=sl,
                tp=tp,
                time_in_force=time_in_force or TimeInForce("gtc"),
            )
        ]

    @classmethod
    def create_new(
        cls,
        *,
        aggregate_id: OrderId,
        intent_id: DecisionId,
        broker_order_ref: BrokerOrderRef,
        symbol: Symbol,
        order_kind: OrderKind,
        side: PositionSide,
        volume: PositiveVolume,
        reference_price: ReferencePrice | None = None,
        stop_price: Price | None = None,
        limit_price: Price | None = None,
        sl: Price | None = None,
        tp: Price | None = None,
        time_in_force: TimeInForce | None = None,
    ) -> tuple[Self, list[BaseEvent]]:
        """
        Canonical factory for a brand-new Order aggregate.

        Returns:
            - the canonical empty aggregate instance
            - the domain event(s) that must be persisted to create it

        Notes:
            - The returned aggregate is intentionally still EMPTY until
              a RecordedEventEnvelope is persisted and applied.
            - This preserves strict event-sourcing discipline:
              state changes only through apply(envelope).
        """

        aggregate = cls.new(aggregate_id=aggregate_id)

        events = cls.decide_create(
            intent_id=intent_id,
            broker_order_ref=broker_order_ref,
            symbol=symbol,
            order_kind=order_kind,
            side=side,
            volume=volume,
            reference_price=reference_price,
            stop_price=stop_price,
            limit_price=limit_price,
            sl=sl,
            tp=tp,
            time_in_force=time_in_force,
        )

        return aggregate, events

    # --- Instance commands (valid only after creation) ------------------------

    def register_fill(self, *, fill: ExecutionFill) -> list[BaseEvent]:
        """
        Registers an execution fill against this order.
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
                broker_order_ref=state.broker_order_ref,
                fill=fill,
            )
        ]

    def cancel(self) -> list[BaseEvent]:
        """
        Cancels the order if it has not yet reached a terminal state.
        """
        state = self.state

        if not isinstance(state, OrderInitializedState):
            raise InvalidStateTransition("Cannot cancel uninitialized order")

        if state.status.is_terminal():
            raise OrderNotFillable("Order already terminal")

        return [
            OrderCancelledEvent(
                broker_order_ref=state.broker_order_ref,
            )
        ]

    # --- Event → State transitions --------------------------------------------

    @staticmethod
    def _apply_created(
        state: OrderStateBase,
        event: BaseEvent,
        envelope: RecordedEventEnvelope,
    ) -> OrderStateBase:
        if not isinstance(state, OrderUninitializedState):
            raise InvariantViolation("Order already created")

        if not isinstance(event, OrderCreatedEvent):
            raise InvariantViolation("Invalid event type")

        return OrderInitializedState(
            last_sequence=envelope.sequence,
            intent_id=event.intent_id,
            broker_order_ref=event.broker_order_ref,
            symbol=event.symbol,
            order_kind=event.order_kind,
            side=event.side,
            requested_volume=event.volume,
            filled_volume=NonNegativeVolume.zero(),
            status=OrderStatus.pending(),
            reference_price=event.reference_price,
            stop_price=event.stop_price,
            limit_price=event.limit_price,
            sl=event.sl,
            tp=event.tp,
            time_in_force=event.time_in_force,
        )

    @staticmethod
    def _apply_fill_registered(
        state: OrderStateBase,
        event: BaseEvent,
        envelope: RecordedEventEnvelope,
    ) -> OrderStateBase:
        if not isinstance(state, OrderInitializedState):
            raise InvariantViolation("Order not initialized")

        if not isinstance(event, OrderFillRegisteredEvent):
            raise InvariantViolation("Invalid event type")

        if event.broker_order_ref != state.broker_order_ref:
            raise InvariantViolation("Illegal fill event: broker_order_id mismatch")

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
            intent_id=state.intent_id,
            broker_order_ref=state.broker_order_ref,
            symbol=state.symbol,
            order_kind=state.order_kind,
            side=state.side,
            requested_volume=state.requested_volume,
            filled_volume=NonNegativeVolume(new_filled),
            status=new_status,
            reference_price=state.reference_price,
            stop_price=state.stop_price,
            limit_price=state.limit_price,
            sl=state.sl,
            tp=state.tp,
            time_in_force=state.time_in_force,
        )

    @staticmethod
    def _apply_cancelled(
        state: OrderStateBase,
        event: BaseEvent,
        envelope: RecordedEventEnvelope,
    ) -> OrderStateBase:
        if not isinstance(state, OrderInitializedState):
            raise InvariantViolation("Order not initialized")

        if not isinstance(event, OrderCancelledEvent):
            raise InvariantViolation("Invalid event type")

        if event.broker_order_ref != state.broker_order_ref:
            raise InvariantViolation("Illegal cancel event: broker_order_id mismatch")

        if state.status.is_terminal():
            raise InvariantViolation("Illegal cancel event: order already terminal")

        return OrderInitializedState(
            last_sequence=envelope.sequence,
            intent_id=state.intent_id,
            broker_order_ref=state.broker_order_ref,
            symbol=state.symbol,
            order_kind=state.order_kind,
            side=state.side,
            requested_volume=state.requested_volume,
            filled_volume=state.filled_volume,
            status=OrderStatus.cancelled(),
            reference_price=state.reference_price,
            stop_price=state.stop_price,
            limit_price=state.limit_price,
            sl=state.sl,
            tp=state.tp,
            time_in_force=state.time_in_force,
        )

    # --- Handler registry -----------------------------------------------------

    @classmethod
    def _handlers(
        cls,
    ) -> Mapping[type[BaseEvent], EventHandler[OrderStateBase, BaseEvent]]:
        return {
            OrderCreatedEvent: cls._apply_created,
            OrderFillRegisteredEvent: cls._apply_fill_registered,
            OrderCancelledEvent: cls._apply_cancelled,
        }
