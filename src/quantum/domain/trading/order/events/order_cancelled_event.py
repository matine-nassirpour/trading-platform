from dataclasses import dataclass
from typing import ClassVar

from quantum.domain.trading.common.events.fact_event import FactEvent
from quantum.domain.trading.identity.broker_order_ref import BrokerOrderRef


@dataclass(frozen=True, slots=True)
class OrderCancelledEvent(FactEvent):
    event_name: ClassVar[str] = "trading.order.cancelled"
    event_version: ClassVar[int] = 1

    broker_order_ref: BrokerOrderRef
