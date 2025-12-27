from dataclasses import dataclass
from typing import ClassVar

from quantum.domain.events.base import BaseEvent
from quantum.domain.model.value_objects.identifiers import IntentId, PositionId
from quantum.domain.model.value_objects.price import Price
from quantum.domain.model.value_objects.symbol import Symbol
from quantum.domain.model.value_objects.time import EpochMs
from quantum.domain.types.enums import App


@dataclass(frozen=True)
class TrailingTriggerEvent(BaseEvent):
    event_name: ClassVar[str] = "trading.trailing_trigger"
    symbol: Symbol

    intent_id: IntentId
    position_id: PositionId

    new_sl: Price

    trigger_epoch_ms: EpochMs
    price_at_trigger: Price
    app: App = App.EA_MQL5
