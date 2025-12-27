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

    def _validate(self) -> None:
        if self.filled_volume.value < 0:
            raise InvalidStateTransition("Filled volume cannot be negative")

        if self.filled_volume.value > self.requested_volume.value:
            raise InvalidStateTransition("Filled volume exceeds requested volume")

        if (
            self.status == OrderStatus.FILLED
            and self.filled_volume != self.requested_volume
        ):
            raise InvalidStateTransition("FILLED order must have full volume")

    def acknowledge(self) -> Order:
        if self.status != OrderStatus.PENDING:
            raise InvalidStateTransition("Only pending orders can be acknowledged")
        return replace(self, status=OrderStatus.ACKED)

    def register_fill(self, volume: Volume) -> Order:
        if self.status not in {OrderStatus.ACKED, OrderStatus.PARTIALLY_FILLED}:
            raise InvalidStateTransition("Order not fillable")

        new_volume = Volume(self.filled_volume.value + volume.value)

        status = (
            OrderStatus.FILLED
            if new_volume.value == self.requested_volume.value
            else OrderStatus.PARTIALLY_FILLED
        )

        return replace(self, filled_volume=new_volume, status=status)
