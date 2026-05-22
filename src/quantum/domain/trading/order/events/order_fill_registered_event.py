from dataclasses import dataclass
from typing import ClassVar

from quantum.domain.trading.common.events.fact_event import FactEvent
from quantum.domain.trading.execution.fills.execution_fill import ExecutionFill
from quantum.domain.trading.identity.broker_order_ref import BrokerOrderRef


@dataclass(frozen=True, slots=True)
class OrderFillRegisteredEvent(FactEvent):
    event_name: ClassVar[str] = "trading.order.fill_registered"
    event_version: ClassVar[int] = 1

    broker_order_ref: BrokerOrderRef
    fill: ExecutionFill
