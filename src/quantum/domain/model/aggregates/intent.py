from __future__ import annotations

from dataclasses import dataclass, replace

from quantum.domain.events.trading.v1.order_ack_event import OrderAckEvent
from quantum.domain.events.trading.v1.order_submit_event import OrderSubmitEvent
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

    def submit(self, at: EpochMs, client_order_id: str) -> TradingIntent:
        if self.submitted:
            raise InvalidStateTransition("Intent already submitted")

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
        updated = []
        found = False

        for o in self.orders:
            if o.order_id == order_id:
                updated.append(o.acknowledge())
                found = True
            else:
                updated.append(o)

        if not found:
            raise InvalidStateTransition("Order not found")

        event = OrderAckEvent(
            occurred_at=at.to_datetime(),
            intent_id=self.intent_id,
            order_id=order_id,
            symbol=self.symbol,
            ack_epoch_ms=at,
        )

        return replace(self, orders=tuple(updated))._raise(event)
