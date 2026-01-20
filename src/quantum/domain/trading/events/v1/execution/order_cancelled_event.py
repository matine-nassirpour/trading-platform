from dataclasses import dataclass
from typing import ClassVar

from quantum.domain.shared_kernel.events.base_event import BaseEvent
from quantum.domain.trading.value_objects.identifiers.order_id import OrderId


@dataclass(frozen=True, slots=True)
class OrderCancelledEvent(BaseEvent):
    event_name: ClassVar[str] = "trading.order.cancelled"
    event_version: ClassVar[int] = 1

    order_id: OrderId
