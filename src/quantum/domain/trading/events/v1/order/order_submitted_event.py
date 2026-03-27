from dataclasses import dataclass
from typing import ClassVar

from quantum.domain.market.instrument.identity.symbol import Symbol
from quantum.domain.shared_kernel.modeling.identity.decision_id import DecisionId
from quantum.domain.trading.events.fact_event import FactEvent


@dataclass(frozen=True, slots=True)
class OrderSubmittedEvent(FactEvent):
    event_name: ClassVar[str] = "trading.order.submitted"
    event_version: ClassVar[int] = 1

    intent_id: DecisionId
    symbol: Symbol
