from __future__ import annotations

from dataclasses import dataclass, replace

from quantum.domain.events.trading.v1.order_ack_event import OrderAckEvent
from quantum.domain.events.trading.v1.order_submit_event import OrderSubmitEvent
from quantum.domain.model.aggregates.base import AggregateRoot
from quantum.domain.model.entities.order import Order
from quantum.domain.model.exceptions.validation_exceptions import (
    InvalidStateTransition,
    InvariantViolation,
)
from quantum.domain.model.value_objects.identifiers import IntentId, OrderId
from quantum.domain.model.value_objects.symbol import Symbol
from quantum.domain.model.value_objects.time import EpochMs
from quantum.domain.model.value_objects.volume import Volume
from quantum.domain.types.order_status import OrderStatus


@dataclass(frozen=True)
class TradingIntent(AggregateRoot):
    """
    Aggregate Root representing a trading intent.

    Invariants:
    - submitted == False  => orders == ()
    - orders != ()        => submitted == True
    - order_id unique within orders
    """

    intent_id: IntentId
    symbol: Symbol
    orders: tuple[Order, ...] = ()
    submitted: bool = False

    # --------------------------------------------------------------------------
    # Invariants
    # --------------------------------------------------------------------------
    def _validate(self) -> None:
        # orders container integrity
        if not isinstance(self.orders, tuple):
            raise InvariantViolation("Orders must be stored as an immutable tuple")

        # submission / orders coherence
        if not self.submitted and self.orders:
            raise InvariantViolation("Orders cannot exist before intent submission")

        if self.submitted and not isinstance(self.orders, tuple):
            raise InvariantViolation("Orders must be a tuple after submission")

        # uniqueness of OrderId
        order_ids = [o.order_id for o in self.orders]
        if len(order_ids) != len(set(order_ids)):
            raise InvariantViolation("Duplicate OrderId detected in TradingIntent")

    # --------------------------------------------------------------------------
    # Commands
    # --------------------------------------------------------------------------
    def submit(self, at: EpochMs, client_order_id: str) -> TradingIntent:
        if self.submitted:
            raise InvalidStateTransition("TradingIntent already submitted")

        event = OrderSubmitEvent(
            occurred_at=at.to_datetime(),
            intent_id=self.intent_id,
            client_order_id=client_order_id,
            symbol=self.symbol,
            request_epoch_ms=at,
        )

        return replace(self, submitted=True)._raise(event)

    def create_order(self, order_id: OrderId, volume: Volume) -> TradingIntent:
        if not self.submitted:
            raise InvalidStateTransition("Cannot create order before submission")

        order = Order(
            order_id=order_id,
            requested_volume=volume,
            filled_volume=Volume.zero(),
            status=OrderStatus.PENDING,
        )

        return replace(self, orders=self.orders + (order,))

    def acknowledge_order(self, order_id: OrderId, at: EpochMs) -> TradingIntent:
        updated_orders = []
        found = False

        for order in self.orders:
            if order.order_id == order_id:
                updated_orders.append(order.acknowledge())
                found = True
            else:
                updated_orders.append(order)

        if not found:
            raise InvalidStateTransition("Order not found in TradingIntent")

        event = OrderAckEvent(
            occurred_at=at.to_datetime(),
            intent_id=self.intent_id,
            order_id=order_id,
            symbol=self.symbol,
            ack_epoch_ms=at,
        )

        return replace(self, orders=tuple(updated_orders))._raise(event)
