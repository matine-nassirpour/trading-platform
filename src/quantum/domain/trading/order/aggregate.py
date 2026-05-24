from collections.abc import Mapping
from dataclasses import dataclass
from typing import Self

from quantum.domain.market.instrument.identity.symbol import Symbol
from quantum.domain.market.instrument.pricing.reference_price import ReferencePrice
from quantum.domain.shared_kernel.event_sourcing.aggregates.event_sourced_aggregate_root import (
    EventHandler,
    EventSourcedAggregateRoot,
)
from quantum.domain.shared_kernel.event_sourcing.events.actor_id import ActorId
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
from quantum.domain.shared_kernel.modeling.temporal.epoch_ms import EpochMs
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
from quantum.domain.trading.execution.reports.execution_rejection import (
    ExecutionRejection,
)
from quantum.domain.trading.identity.broker_order_ref import BrokerOrderRef
from quantum.domain.trading.order.cancellation.order_cancellation_origin import (
    OrderCancellationOrigin,
)
from quantum.domain.trading.order.cancellation.order_cancellation_reason import (
    OrderCancellationReason,
)
from quantum.domain.trading.order.events.order_accepted_event import OrderAcceptedEvent
from quantum.domain.trading.order.events.order_acknowledged_event import (
    OrderAcknowledgedEvent,
)
from quantum.domain.trading.order.events.order_cancelled_event import (
    OrderCancelledEvent,
)
from quantum.domain.trading.order.events.order_created_event import OrderCreatedEvent
from quantum.domain.trading.order.events.order_expired_event import OrderExpiredEvent
from quantum.domain.trading.order.events.order_fill_registered_event import (
    OrderFillRegisteredEvent,
)
from quantum.domain.trading.order.events.order_rejected_event import OrderRejectedEvent
from quantum.domain.trading.order.events.order_submitted_event import (
    OrderSubmittedEvent,
)
from quantum.domain.trading.order.order_kind import OrderKind
from quantum.domain.trading.order.states.order_initialized_state import (
    OrderInitializedState,
)
from quantum.domain.trading.order.states.order_state_base import OrderStateBase
from quantum.domain.trading.order.states.order_uninitialized_state import (
    OrderUninitializedState,
)
from quantum.domain.trading.order.status.order_fill_status import OrderFillStatus
from quantum.domain.trading.order.status.order_lifecycle_status import (
    OrderLifecycleStatus,
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
        decision_id: DecisionId,
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
                decision_id=decision_id,
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
        decision_id: DecisionId,
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
            decision_id=decision_id,
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

    def submit(
        self,
        *,
        submitted_by: ActorId,
    ) -> list[BaseEvent]:
        state = self.state

        if not isinstance(state, OrderInitializedState):
            raise InvalidStateTransition("Cannot submit uninitialized order")

        if state.lifecycle_status != OrderLifecycleStatus.created():
            raise InvalidStateTransition("Only created orders can be submitted")

        return [
            OrderSubmittedEvent(
                broker_order_ref=state.broker_order_ref,
                decision_id=state.decision_id,
                symbol=state.symbol,
                submitted_by=submitted_by,
            )
        ]

    def acknowledge(self) -> list[BaseEvent]:
        state = self.state

        if not isinstance(state, OrderInitializedState):
            raise InvalidStateTransition("Cannot acknowledge uninitialized order")

        if state.lifecycle_status != OrderLifecycleStatus.submitted():
            raise InvalidStateTransition("Only submitted orders can be acknowledged")

        return [
            OrderAcknowledgedEvent(
                decision_id=state.decision_id,
                broker_order_ref=state.broker_order_ref,
                symbol=state.symbol,
            )
        ]

    def accept(self) -> list[BaseEvent]:
        state = self.state

        if not isinstance(state, OrderInitializedState):
            raise InvalidStateTransition("Cannot accept uninitialized order")

        if state.lifecycle_status != OrderLifecycleStatus.acknowledged():
            raise InvalidStateTransition("Only acknowledged orders can be accepted")

        return [
            OrderAcceptedEvent(
                broker_order_ref=state.broker_order_ref,
            )
        ]

    def reject(self, *, rejection: ExecutionRejection) -> list[BaseEvent]:
        state = self.state

        if not isinstance(state, OrderInitializedState):
            raise InvalidStateTransition("Cannot reject uninitialized order")

        if state.lifecycle_status.is_terminal():
            raise OrderNotFillable("Order lifecycle is already terminal")

        if state.fill_status.is_filled():
            raise OrderNotFillable("Fully filled order cannot be rejected")

        return [
            OrderRejectedEvent(
                broker_order_ref=state.broker_order_ref,
                decision_id=state.decision_id,
                symbol=state.symbol,
                rejection=rejection,
            )
        ]

    def expire(self) -> list[BaseEvent]:
        state = self.state

        if not isinstance(state, OrderInitializedState):
            raise InvalidStateTransition("Cannot expire uninitialized order")

        if state.lifecycle_status.is_terminal():
            raise OrderNotFillable("Order lifecycle is already terminal")

        if state.fill_status.is_filled():
            raise OrderNotFillable("Fully filled order cannot expire")

        return [
            OrderExpiredEvent(
                broker_order_ref=state.broker_order_ref,
            )
        ]

    def register_fill(self, *, fill: ExecutionFill) -> list[BaseEvent]:
        """
        Registers an execution fill against this order.
        """
        state = self.state

        if not isinstance(state, OrderInitializedState):
            raise InvalidStateTransition("Cannot fill uninitialized order")

        if not state.lifecycle_status.can_receive_fill():
            raise OrderNotFillable("Order lifecycle cannot receive fills")

        if state.fill_status.is_filled():
            raise OrderNotFillable("Order is already fully filled")

        new_total = state.filled_volume.value + fill.volume.value

        if new_total > state.requested_volume.value:
            raise OrderOverfill("Fill exceeds remaining order volume")

        if fill.link.broker_order_ref != state.broker_order_ref:
            raise InvariantViolation("Fill broker_order_ref mismatch")

        return [
            OrderFillRegisteredEvent(
                broker_order_ref=state.broker_order_ref,
                fill=fill,
            )
        ]

    def cancel(
        self,
        *,
        cancelled_by: ActorId,
        reason: OrderCancellationReason,
        origin: OrderCancellationOrigin,
        cancelled_at: EpochMs,
        comment: str | None = None,
    ) -> list[BaseEvent]:
        """
        Cancels the order if it has not yet reached a terminal state.
        """
        state = self.state

        if not isinstance(state, OrderInitializedState):
            raise InvalidStateTransition("Cannot cancel uninitialized order")

        if state.lifecycle_status.is_terminal():
            raise OrderNotFillable("Order lifecycle is already terminal")

        if state.fill_status.is_filled():
            raise OrderNotFillable("Fully filled order cannot be cancelled")

        return [
            OrderCancelledEvent(
                broker_order_ref=state.broker_order_ref,
                cancelled_by=cancelled_by,
                reason=reason,
                origin=origin,
                cancelled_at=cancelled_at,
                comment=comment,
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
            decision_id=event.decision_id,
            broker_order_ref=event.broker_order_ref,
            symbol=event.symbol,
            order_kind=event.order_kind,
            side=event.side,
            requested_volume=event.volume,
            filled_volume=NonNegativeVolume.zero(),
            lifecycle_status=OrderLifecycleStatus.created(),
            fill_status=OrderFillStatus.unfilled(),
            reference_price=event.reference_price,
            stop_price=event.stop_price,
            limit_price=event.limit_price,
            sl=event.sl,
            tp=event.tp,
            time_in_force=event.time_in_force,
        )

    @staticmethod
    def _apply_submitted(
        state: OrderStateBase,
        event: BaseEvent,
        envelope: RecordedEventEnvelope,
    ) -> OrderStateBase:
        if not isinstance(state, OrderInitializedState):
            raise InvariantViolation("Order not initialized")

        if not isinstance(event, OrderSubmittedEvent):
            raise InvariantViolation("Invalid event type")

        if state.lifecycle_status != OrderLifecycleStatus.created():
            raise InvariantViolation("Only created orders can become submitted")

        return state.with_lifecycle_status(
            lifecycle_status=OrderLifecycleStatus.submitted(),
            last_sequence=envelope.sequence,
        )

    @staticmethod
    def _apply_acknowledged(
        state: OrderStateBase,
        event: BaseEvent,
        envelope: RecordedEventEnvelope,
    ) -> OrderStateBase:
        if not isinstance(state, OrderInitializedState):
            raise InvariantViolation("Order not initialized")

        if not isinstance(event, OrderAcknowledgedEvent):
            raise InvariantViolation("Invalid event type")

        if event.broker_order_ref != state.broker_order_ref:
            raise InvariantViolation(
                "Illegal acknowledge event: broker_order_id mismatch"
            )

        if state.lifecycle_status != OrderLifecycleStatus.submitted():
            raise InvariantViolation("Only submitted orders can become acknowledged")

        return state.with_lifecycle_status(
            lifecycle_status=OrderLifecycleStatus.acknowledged(),
            last_sequence=envelope.sequence,
        )

    @staticmethod
    def _apply_accepted(
        state: OrderStateBase,
        event: BaseEvent,
        envelope: RecordedEventEnvelope,
    ) -> OrderStateBase:
        if not isinstance(state, OrderInitializedState):
            raise InvariantViolation("Order not initialized")

        if not isinstance(event, OrderAcceptedEvent):
            raise InvariantViolation("Invalid event type")

        if event.broker_order_ref != state.broker_order_ref:
            raise InvariantViolation("Illegal accept event: broker_order_id mismatch")

        if state.lifecycle_status != OrderLifecycleStatus.acknowledged():
            raise InvariantViolation("Only acknowledged orders can become accepted")

        return state.with_lifecycle_status(
            lifecycle_status=OrderLifecycleStatus.accepted(),
            last_sequence=envelope.sequence,
        )

    @staticmethod
    def _apply_rejected(
        state: OrderStateBase,
        event: BaseEvent,
        envelope: RecordedEventEnvelope,
    ) -> OrderStateBase:
        if not isinstance(state, OrderInitializedState):
            raise InvariantViolation("Order not initialized")

        if not isinstance(event, OrderRejectedEvent):
            raise InvariantViolation("Invalid event type")

        if event.broker_order_ref != state.broker_order_ref:
            raise InvariantViolation("Illegal reject event: broker_order_id mismatch")

        if state.lifecycle_status.is_terminal():
            raise OrderNotFillable("Order lifecycle is already terminal")

        if state.fill_status.is_filled():
            raise OrderNotFillable("Fully filled order cannot be rejected")

        return state.with_lifecycle_status(
            lifecycle_status=OrderLifecycleStatus.rejected(),
            last_sequence=envelope.sequence,
        )

    @staticmethod
    def _apply_expired(
        state: OrderStateBase,
        event: BaseEvent,
        envelope: RecordedEventEnvelope,
    ) -> OrderStateBase:
        if not isinstance(state, OrderInitializedState):
            raise InvariantViolation("Order not initialized")

        if not isinstance(event, OrderExpiredEvent):
            raise InvariantViolation("Invalid event type")

        if event.broker_order_ref != state.broker_order_ref:
            raise InvariantViolation("Illegal expire event: broker_order_id mismatch")

        if state.lifecycle_status.is_terminal():
            raise OrderNotFillable("Order lifecycle is already terminal")

        if state.fill_status.is_filled():
            raise OrderNotFillable("Fully filled order cannot expire")

        return state.with_lifecycle_status(
            lifecycle_status=OrderLifecycleStatus.expired(),
            last_sequence=envelope.sequence,
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

        if event.fill.link.broker_order_ref != state.broker_order_ref:
            raise InvariantViolation("Illegal fill event: fill link order mismatch")

        if not state.lifecycle_status.can_receive_fill():
            raise OrderNotFillable("Order lifecycle cannot receive fills")

        if state.fill_status.is_filled():
            raise OrderNotFillable("Order is already fully filled")

        new_filled = state.filled_volume.value + event.fill.volume.value

        if new_filled > state.requested_volume.value:
            raise InvariantViolation("Illegal fill event: overfill")

        new_fill_status = (
            OrderFillStatus.filled()
            if new_filled == state.requested_volume.value
            else OrderFillStatus.partially_filled()
        )

        new_lifecycle_status = (
            OrderLifecycleStatus.completed()
            if new_fill_status.is_filled()
            else state.lifecycle_status
        )

        return state.with_registered_fill(
            last_sequence=envelope.sequence,
            filled_volume=NonNegativeVolume(new_filled),
            fill_status=new_fill_status,
            lifecycle_status=new_lifecycle_status,
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

        if state.lifecycle_status.is_terminal():
            raise OrderNotFillable("Order lifecycle is already terminal")

        if state.fill_status.is_filled():
            raise OrderNotFillable("Fully filled order cannot be cancelled")

        return state.with_lifecycle_status(
            lifecycle_status=OrderLifecycleStatus.cancelled(),
            last_sequence=envelope.sequence,
        )

    # --- Handler registry -----------------------------------------------------

    @classmethod
    def _handlers(
        cls,
    ) -> Mapping[type[BaseEvent], EventHandler[OrderStateBase, BaseEvent]]:
        return {
            OrderCreatedEvent: cls._apply_created,
            OrderSubmittedEvent: cls._apply_submitted,
            OrderAcknowledgedEvent: cls._apply_acknowledged,
            OrderAcceptedEvent: cls._apply_accepted,
            OrderRejectedEvent: cls._apply_rejected,
            OrderExpiredEvent: cls._apply_expired,
            OrderFillRegisteredEvent: cls._apply_fill_registered,
            OrderCancelledEvent: cls._apply_cancelled,
        }
