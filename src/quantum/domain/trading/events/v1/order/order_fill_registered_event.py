from dataclasses import dataclass
from typing import ClassVar

from quantum.domain.shared_kernel.events.base.fact_event import FactEvent
from quantum.domain.shared_kernel.identifiers.broker_order_id import BrokerOrderId
from quantum.domain.trading.execution.order.execution_fill import ExecutionFill


@dataclass(frozen=True, slots=True)
class OrderFillRegisteredEvent(FactEvent):
    event_name: ClassVar[str] = "trading.order.fill_registered"
    event_version: ClassVar[int] = 1

    order_id: BrokerOrderId
    fill: ExecutionFill
