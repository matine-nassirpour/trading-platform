from dataclasses import dataclass
from typing import ClassVar

from quantum.domain.shared.events.base_event import BaseEvent
from quantum.domain.shared.value_objects.epoch_ms import EpochMs
from quantum.domain.shared.value_objects.symbol import Symbol
from quantum.domain.trading.value_objects.identifiers import IntentId
from quantum.domain.trading.value_objects.volume import PositiveVolume


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
    decision_epoch_ms: EpochMs
