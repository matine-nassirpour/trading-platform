from dataclasses import dataclass
from typing import ClassVar, Literal

from quantum.domain.events.base import BaseEvent
from quantum.domain.model.value_objects.identifiers import IntentId, PositionId
from quantum.domain.model.value_objects.price import Price
from quantum.domain.model.value_objects.symbol import Symbol
from quantum.domain.model.value_objects.time import EpochMs
from quantum.domain.types.enums import App


@dataclass(frozen=True)
class SlTpUpdateEvent(BaseEvent):
    event_name: ClassVar[str] = "trading.sl_tp_update"
    event_version: ClassVar[int] = 1
    symbol: Symbol
    position_id: PositionId
    update_epoch_ms: EpochMs
    reason: Literal["manual", "rule", "risk"]
    intent_id: IntentId | None = None
    old_sl: Price | None = None
    new_sl: Price | None = None
    old_tp: Price | None = None
    new_tp: Price | None = None
    app: App = App.EA_MQL5
