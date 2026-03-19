from dataclasses import dataclass
from typing import ClassVar

from quantum.domain.market.instrument.symbol import Symbol
from quantum.domain.shared_kernel.identity.intent_id import IntentId
from quantum.domain.trading.events.fact_event import FactEvent


@dataclass(frozen=True, slots=True)
class OrderSubmittedEvent(FactEvent):
    event_name: ClassVar[str] = "trading.order.submitted"
    event_version: ClassVar[int] = 1

    intent_id: IntentId
    symbol: Symbol
