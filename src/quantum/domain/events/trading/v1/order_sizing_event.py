from dataclasses import dataclass
from typing import ClassVar

from quantum.domain.events.base import BaseEvent
from quantum.domain.model.value_objects.identifiers import IntentId
from quantum.domain.model.value_objects.symbol import Symbol
from quantum.domain.model.value_objects.time import EpochMs
from quantum.domain.model.value_objects.volume import PositiveVolume


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
