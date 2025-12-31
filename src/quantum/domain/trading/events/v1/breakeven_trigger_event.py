from dataclasses import dataclass
from typing import ClassVar

from quantum.domain.shared.events.base_event import BaseEvent
from quantum.domain.shared.value_objects.epoch_ms import EpochMs
from quantum.domain.shared.value_objects.symbol import Symbol
from quantum.domain.trading.value_objects.identifiers import IntentId, PositionId
from quantum.domain.trading.value_objects.price import Price


@dataclass(frozen=True)
class BreakevenTriggerEvent(BaseEvent):
    event_name: ClassVar[str] = "trading.breakeven_trigger"
    event_version: ClassVar[int] = 1
    intent_id: IntentId
    position_id: PositionId
    symbol: Symbol
    price_at_trigger: Price
    trigger_epoch_ms: EpochMs
