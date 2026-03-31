from dataclasses import dataclass
from typing import ClassVar

from quantum.domain.trading.common.events.fact_event import FactEvent
from quantum.domain.trading.execution.order.execution_fill import ExecutionFill
from quantum.domain.trading.identifiers.broker_order_id import BrokerOrderId


@dataclass(frozen=True, slots=True)
class OrderFillRegisteredEvent(FactEvent):
    event_name: ClassVar[str] = "trading.order.fill_registered"
    event_version: ClassVar[int] = 1

    broker_order_id: BrokerOrderId
    fill: ExecutionFill
