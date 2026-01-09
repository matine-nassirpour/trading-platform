from __future__ import annotations

from decimal import Decimal

from quantum.domain.shared_kernel.errors.invariants import InvariantViolation
from quantum.domain.shared_kernel.errors.order_errors import (
    OrderNotFillable,
    OrderOverfill,
)
from quantum.domain.shared_kernel.primitives.event_sourced_aggregate_root import (
    EventSourcedAggregateRoot,
)
from quantum.domain.shared_kernel.value_objects.epoch_ms import EpochMs
from quantum.domain.shared_kernel.value_objects.volume import (
    NonNegativeVolume,
    PositiveVolume,
)
from quantum.domain.trading.events.v1.order_cancelled_event import OrderCancelledEvent
from quantum.domain.trading.events.v1.order_created_event import OrderCreatedEvent
from quantum.domain.trading.events.v1.order_fill_registered_event import (
    OrderFillRegisteredEvent,
)
from quantum.domain.trading.execution.order.execution_fill import ExecutionFill
from quantum.domain.trading.execution.order.order_status import OrderStatus
from quantum.domain.trading.execution.order.order_type import OrderType
from quantum.domain.trading.execution.order.position_side import PositionSide
from quantum.domain.trading.value_objects.identifiers.order_id import OrderId


class Order(EventSourcedAggregateRoot):
    """
    Canonical event-sourced Order aggregate.
    """

    _order_id: OrderId
    _order_type: OrderType
    _side: PositionSide
    _requested_volume: PositiveVolume
    _fills: tuple[ExecutionFill, ...]
    _status: OrderStatus

    # --- Factory --------------------------------------------------------------

    @staticmethod
    def create(
        *,
        intent_id,
        order_id: OrderId,
        symbol,
        order_type: OrderType,
        side: PositionSide,
        volume: PositiveVolume,
        occurred_at: EpochMs,
    ) -> Order:
        order = Order()
        order._raise(
            OrderCreatedEvent(
                occurred_at=occurred_at,
                intent_id=intent_id,
                order_id=order_id,
                symbol=symbol,
                order_type=order_type,
                side=side,
                volume=volume,
            )
        )
        return order

    # --- Commands -------------------------------------------------------------

    def register_fill(self, *, fill: ExecutionFill) -> None:
        if not self._status.is_fillable():
            raise OrderNotFillable("Order not fillable")

        if fill.volume.value > self.remaining_volume.value:
            raise OrderOverfill("Fill exceeds remaining volume")

        self._raise(
            OrderFillRegisteredEvent(
                occurred_at=fill.executed_at,
                order_id=self._order_id,
                fill=fill,
            )
        )

    def cancel(self, *, occurred_at: EpochMs) -> None:
        if self._status.is_terminal():
            raise OrderNotFillable("Order already terminal")

        self._raise(
            OrderCancelledEvent(
                occurred_at=occurred_at,
                order_id=self._order_id,
            )
        )

    # --- Derived properties ---------------------------------------------------

    @property
    def remaining_volume(self) -> NonNegativeVolume:
        remaining = self._requested_volume.value - self.filled_volume.value
        return NonNegativeVolume(remaining)

    @property
    def filled_volume(self) -> NonNegativeVolume:
        total = sum((f.volume.value for f in self._fills), start=Decimal("0"))
        return NonNegativeVolume(total)

    # --- Event application ----------------------------------------------------

    def _apply_ordercreatedevent(self, event: OrderCreatedEvent) -> None:
        self._order_id = event.order_id
        self._order_type = event.order_type
        self._side = event.side
        self._requested_volume = event.volume
        self._fills = ()
        self._status = OrderStatus.pending()

    def _apply_orderfillregisteredevent(self, event: OrderFillRegisteredEvent) -> None:
        self._fills = self._fills + (event.fill,)
        self._status = (
            OrderStatus.filled()
            if self.remaining_volume.value == Decimal("0")
            else OrderStatus.partially_filled()
        )

    def _apply_ordercancelledevent(self, event: OrderCancelledEvent) -> None:
        self._status = OrderStatus.cancelled()

    # --- Aggregate invariants -------------------------------------------------

    def _validate_state(self) -> None:
        self._assert_identity()
        self._assert_structure()
        self._assert_volume_integrity()
        self._assert_status_consistency()

    def _assert_identity(self) -> None:
        if not isinstance(self._order_id, OrderId):
            raise InvariantViolation("OrderId missing")

    def _assert_structure(self) -> None:
        if not isinstance(self._order_type, OrderType):
            raise InvariantViolation("OrderType missing")

        if not isinstance(self._side, PositionSide):
            raise InvariantViolation("PositionSide missing")

        if not isinstance(self._requested_volume, PositiveVolume):
            raise InvariantViolation("Requested volume missing")

        if not isinstance(self._status, OrderStatus):
            raise InvariantViolation("OrderStatus missing")

    def _assert_volume_integrity(self) -> None:
        filled = sum(f.volume.value for f in self._fills)

        if filled < 0:
            raise InvariantViolation("Filled volume cannot be negative")

        if filled > self._requested_volume.value:
            raise InvariantViolation("Order overfilled")

    def _assert_status_consistency(self) -> None:
        filled = sum(f.volume.value for f in self._fills)

        if self._status.is_filled() and filled != self._requested_volume.value:
            raise InvariantViolation("Filled order must be fully filled")

        if self._status.is_cancelled() and filled == self._requested_volume.value:
            raise InvariantViolation("Cancelled order cannot be fully filled")
