from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from quantum.domain.shared_kernel.errors.order_errors import (
    OrderNotFillable,
    OrderOverfill,
)
from quantum.domain.shared_kernel.primitives.event_sourced_aggregate_root import (
    EventSourcedAggregateRoot,
)
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


@dataclass(eq=False)
class Order(EventSourcedAggregateRoot):
    """
    Entity representing an order.

    Identity:
    - OrderId
    """

    order_id: OrderId
    order_type: OrderType
    side: PositionSide

    requested_volume: PositiveVolume | None = None
    fills: tuple[ExecutionFill, ...] = ()
    status: OrderStatus | None = None

    # --- Commands -------------------------------------------------------------

    def register_fill(self, *, fill: ExecutionFill) -> None:
        if not self.status.is_fillable():
            raise OrderNotFillable(f"Order {self.order_id} not fillable")

        if fill.volume.value > self.remaining_volume.value:
            raise OrderOverfill("Execution fill exceeds remaining order volume")

        self._raise(
            OrderFillRegisteredEvent(
                occurred_at=fill.executed_at,
                order_id=self.order_id,
                fill=fill,
            )
        )

    def cancel(self, *, occurred_at) -> None:
        if self.status.is_terminal():
            raise OrderNotFillable("Order already terminal")

        self._raise(
            OrderCancelledEvent(
                occurred_at=occurred_at,
                order_id=self.order_id,
            )
        )

    # --- Properties  ----------------------------------------------------------

    @property
    def filled_volume(self) -> NonNegativeVolume:
        total = sum(
            (fill.volume.value for fill in self.fills),
            start=Decimal("0"),
        )
        return NonNegativeVolume(total)

    @property
    def remaining_volume(self) -> NonNegativeVolume:
        remaining = self.requested_volume.value - self.filled_volume.value
        return NonNegativeVolume(remaining)

    # --- Event application ----------------------------------------------------

    def _apply_order_created_event(self, event: OrderCreatedEvent) -> None:
        self.order_id = event.order_id
        self.requested_volume = event.volume
        self.fills = ()
        self.status = OrderStatus.pending()

    def _apply_order_fill_registered_event(
        self, event: OrderFillRegisteredEvent
    ) -> None:
        self.fills = self.fills + (event.fill,)

        self.status = (
            OrderStatus.filled()
            if self.remaining_volume.value == Decimal("0")
            else OrderStatus.partially_filled()
        )

    def _apply_order_cancelled_event(self, event: OrderCancelledEvent) -> None:
        self.status = OrderStatus.cancelled()
