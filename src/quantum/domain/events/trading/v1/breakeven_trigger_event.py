from dataclasses import dataclass
from decimal import Decimal
from typing import ClassVar

from quantum.domain.events.base import BaseEvent
from quantum.domain.model.value_objects.identifiers import IntentId, PositionId
from quantum.domain.model.value_objects.symbol import Symbol
from quantum.domain.model.value_objects.time import EpochMs
from quantum.domain.types.enums import App


@dataclass(frozen=True)
class BreakevenTriggerEvent(BaseEvent):
    event_name: ClassVar[str] = "trading.breakeven_trigger"
    symbol: Symbol
    position_id: PositionId
    intent_id: IntentId
    trigger_epoch_ms: EpochMs
    price_at_trigger: Decimal
    app: App = App.EA_MQL5
