from dataclasses import dataclass
from typing import ClassVar

from quantum.domain.trading.common.events.fact_event import FactEvent
from quantum.domain.trading.identity.broker_order_ref import BrokerOrderRef


@dataclass(frozen=True, slots=True)
class OrderAcceptedEvent(FactEvent):
    """
    - The order was received by an external platform.
    - Not yet executed.
    - Not yet accepted economically.
    """

    event_name: ClassVar[str] = "trading.order.accepted"
    event_version: ClassVar[int] = 1

    broker_order_ref: BrokerOrderRef
