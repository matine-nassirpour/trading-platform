from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import UTC, datetime

from quantum.domain.events.trading.v1.order_ack_event import OrderAckEvent
from quantum.domain.model.aggregates.base import AggregateRoot
from quantum.domain.model.entities.order import Order
from quantum.domain.model.exceptions import InvalidStateTransition
from quantum.domain.model.value_objects.identifiers import IntentId, OrderId
from quantum.domain.model.value_objects.symbol import Symbol
from quantum.domain.model.value_objects.time import EpochMs
from quantum.domain.model.value_objects.volume import Volume
from quantum.domain.types.order_status import OrderStatus


@dataclass(frozen=True)
class TradingIntent(AggregateRoot):
    intent_id: IntentId
    symbol: Symbol
    orders: tuple[Order, ...] = ()
    submitted: bool = False

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

    def acknowledge_order(
        self, order_id: OrderId, ack_epoch_ms: EpochMs
    ) -> TradingIntent:
        updated_orders = []
        for order in self.orders:
            if order.order_id == order_id:
                updated_orders.append(order.with_acknowledged())
            else:
                updated_orders.append(order)

        event = OrderAckEvent(
            occurred_at=datetime.now(UTC),
            intent_id=self.intent_id,
            order_id=order_id,
            symbol=self.symbol,
            ack_epoch_ms=ack_epoch_ms,
        )

        return replace(self, orders=tuple(updated_orders))._raise(event)
