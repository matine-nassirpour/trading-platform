from dataclasses import dataclass
from typing import ClassVar

from quantum.domain.trading.events.fact_event import FactEvent
from quantum.domain.trading.identifiers.broker_order_id import BrokerOrderId


@dataclass(frozen=True, slots=True)
class OrderCancelledEvent(FactEvent):
    event_name: ClassVar[str] = "trading.order.cancelled"
    event_version: ClassVar[int] = 1

    broker_order_id: BrokerOrderId
