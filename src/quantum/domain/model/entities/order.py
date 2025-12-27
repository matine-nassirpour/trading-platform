from __future__ import annotations

from dataclasses import dataclass, replace

from quantum.domain.model.exceptions import InvalidStateTransition
from quantum.domain.model.value_objects.identifiers import OrderId
from quantum.domain.model.value_objects.volume import Volume
from quantum.domain.types.order_status import OrderStatus


@dataclass(frozen=True)
class Order:
    order_id: OrderId
    requested_volume: Volume
    filled_volume: Volume
    status: OrderStatus

    def register_fill(self, volume: Volume) -> Order:
        if self.status not in {OrderStatus.ACKED, OrderStatus.PARTIALLY_FILLED}:
            raise InvalidStateTransition("Order not fillable")

        new_volume = Volume(self.filled_volume.value + volume.value)

        if new_volume.value > self.requested_volume.value:
            raise InvalidStateTransition("Overfill")

        status = (
            OrderStatus.FILLED
            if new_volume.value == self.requested_volume.value
            else OrderStatus.PARTIALLY_FILLED
        )

        return replace(self, filled_volume=new_volume, status=status)
