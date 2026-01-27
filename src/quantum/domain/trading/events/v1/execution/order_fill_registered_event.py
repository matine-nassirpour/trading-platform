from dataclasses import dataclass
from typing import ClassVar

from quantum.domain.shared_kernel.events.base_event import BaseEvent
from quantum.domain.shared_kernel.identifiers.order_id import OrderId
from quantum.domain.trading.execution.order.execution_fill import ExecutionFill


@dataclass(frozen=True, slots=True)
class OrderFillRegisteredEvent(BaseEvent):
    event_name: ClassVar[str] = "trading.order.fill_registered"
    event_version: ClassVar[int] = 1

    order_id: OrderId
    fill: ExecutionFill
