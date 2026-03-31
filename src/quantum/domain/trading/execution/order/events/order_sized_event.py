from dataclasses import dataclass
from typing import ClassVar

from quantum.domain.market.instrument.identity.symbol import Symbol
from quantum.domain.shared_kernel.modeling.identity.decision_id import DecisionId
from quantum.domain.trading.common.events.fact_event import FactEvent
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

    intent_id: DecisionId
    symbol: Symbol
    volume: PositiveVolume
    sizing_model: str
