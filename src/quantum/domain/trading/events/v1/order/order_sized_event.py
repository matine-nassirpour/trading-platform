from dataclasses import dataclass
from typing import ClassVar

from quantum.domain.market.instrument.symbol import Symbol
from quantum.domain.shared_kernel.modeling.identity.intent_id import IntentId
from quantum.domain.trading.events.fact_event import FactEvent
from quantum.domain.trading.value_objects.volume import PositiveVolume


@dataclass(frozen=True, slots=True)
class OrderSizedEvent(FactEvent):
    """
    Emitted when an order volume is determined by a sizing logic.

    Audit meaning:
    - sizing model decision
    """

    event_name: ClassVar[str] = "trading.order.sized"
    event_version: ClassVar[int] = 1

    intent_id: IntentId
    symbol: Symbol
    volume: PositiveVolume
    sizing_model: str
