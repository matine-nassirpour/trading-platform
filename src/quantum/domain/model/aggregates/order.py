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
        if self.status not in (OrderStatus.ACKED, OrderStatus.PARTIALLY_FILLED):
            raise InvalidStateTransition("Cannot fill order in this state")

        if self.filled_volume is None:
            self.filled_volume = fill_volume
        else:
            self.filled_volume = Volume(self.filled_volume.value + fill_volume.value)

        if self.filled_volume.value >= self.requested_volume.value:
            self.status = OrderStatus.FILLED
        else:
            self.status = OrderStatus.PARTIALLY_FILLED
