from __future__ import annotations

from dataclasses import dataclass, replace
from decimal import Decimal

from quantum.domain.model.aggregates.base import AggregateRoot
from quantum.domain.model.exceptions import InvalidStateTransition
from quantum.domain.model.value_objects.identifiers import IntentId, OrderId
from quantum.domain.model.value_objects.volume import Volume
from quantum.domain.types.order_status import OrderStatus


@dataclass(frozen=True)
class Order(AggregateRoot):
    order_id: OrderId
    intent_id: IntentId
    requested_volume: Volume
    filled_volume: Volume
    status: OrderStatus

    @staticmethod
    def new(order_id: OrderId, intent_id: IntentId, volume: Volume) -> Order:
        return Order(
            order_id=order_id,
            intent_id=intent_id,
            requested_volume=volume,
            filled_volume=Volume(Decimal("0")),
            status=OrderStatus.PENDING,
        )

    def acknowledge(self) -> Order:
        if self.status is not OrderStatus.PENDING:
            raise InvalidStateTransition("Order cannot be acknowledged")
        return replace(self, status=OrderStatus.ACKED)

    def register_fill(self, fill_volume: Volume) -> Order:
        if self.status not in {OrderStatus.ACKED, OrderStatus.PARTIALLY_FILLED}:
            raise InvalidStateTransition("Order not fillable")

        new_volume = Volume(self.filled_volume.value + fill_volume.value)
        if new_volume.value > self.requested_volume.value:
            raise InvalidStateTransition("Overfill detected")

        new_status = (
            OrderStatus.FILLED
            if new_volume.value == self.requested_volume.value
            else OrderStatus.PARTIALLY_FILLED
        )

        return replace(
            self,
            filled_volume=new_volume,
            status=new_status,
        )
