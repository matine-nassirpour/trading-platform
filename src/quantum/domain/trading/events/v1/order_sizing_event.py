from dataclasses import dataclass
from typing import ClassVar

from quantum.domain.shared_kernel.events.base_event import BaseEvent
from quantum.domain.shared_kernel.value_objects.symbol import Symbol
from quantum.domain.shared_kernel.value_objects.volume import PositiveVolume
from quantum.domain.trading.value_objects.identifiers.intent_id import IntentId


@dataclass(frozen=True)
class OrderSizingEvent(BaseEvent):
    """
    Emitted when an order volume is determined by a sizing logic.

    Audit meaning:
    - sizing model decision
    """

    event_name: ClassVar[str] = "trading.order_sizing"
    event_version: ClassVar[int] = 1

    intent_id: IntentId
    symbol: Symbol
    volume: PositiveVolume
    sizing_model: str
