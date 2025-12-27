from dataclasses import dataclass
from enum import Enum

from quantum.domain.model.exceptions import InvalidStateTransition
from quantum.domain.model.value_objects.identifiers import IntentId, OrderId
from quantum.domain.model.value_objects.volume import Volume


class OrderStatus(Enum):
    PENDING = "pending"
    ACKED = "acked"
    PARTIALLY_FILLED = "partially_filled"
    FILLED = "filled"
    REJECTED = "rejected"
    CANCELLED = "cancelled"


@dataclass
class Order:
    """
    Aggregate Root.
    """

    order_id: OrderId
    intent_id: IntentId
    requested_volume: Volume
    filled_volume: Volume | None = None
    status: OrderStatus = OrderStatus.PENDING

    def acknowledge(self) -> None:
        if self.status is not OrderStatus.PENDING:
            raise InvalidStateTransition("Order cannot be acknowledged")
        self.status = OrderStatus.ACKED

    def register_fill(self, fill_volume: Volume) -> None:
        if fill_volume.value <= 0:
            raise InvalidStateTransition("Fill volume must be positive")

        if self.status not in {OrderStatus.ACKED, OrderStatus.PARTIALLY_FILLED}:
            raise InvalidStateTransition("Order not fillable in this state")

        new_volume = (
            fill_volume
            if self.filled_volume is None
            else Volume(self.filled_volume.value + fill_volume.value)
        )

        if new_volume.value > self.requested_volume.value:
            raise InvalidStateTransition("Overfill detected")

        self.filled_volume = new_volume
        self.status = (
            OrderStatus.FILLED
            if new_volume.value == self.requested_volume.value
            else OrderStatus.PARTIALLY_FILLED
        )
