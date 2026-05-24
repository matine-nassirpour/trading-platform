from dataclasses import dataclass
from typing import ClassVar

from quantum.domain.market.instrument.identity.symbol import Symbol
from quantum.domain.shared_kernel.modeling.identity.decision_id import DecisionId
from quantum.domain.trading.common.events.fact_event import FactEvent
from quantum.domain.trading.identity.broker_order_ref import BrokerOrderRef


@dataclass(frozen=True, slots=True)
class OrderAcknowledgedEvent(FactEvent):
    """
    - The order was received by an external platform.
    - Not yet executed.
    - Not yet accepted economically.
    """

    event_name: ClassVar[str] = "trading.order.acknowledged"
    event_version: ClassVar[int] = 1

    decision_id: DecisionId
    broker_order_ref: BrokerOrderRef
    symbol: Symbol
