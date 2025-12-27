from dataclasses import dataclass
from typing import ClassVar

from quantum.domain.events.base import BaseEvent
from quantum.domain.model.value_objects.identifiers import IntentId, PositionId
from quantum.domain.model.value_objects.money import Money
from quantum.domain.model.value_objects.price import Price
from quantum.domain.model.value_objects.symbol import Symbol
from quantum.domain.model.value_objects.time import EpochMs
from quantum.domain.model.value_objects.volume import Volume
from quantum.domain.types.enums import App


@dataclass(frozen=True)
class PositionUpdateEvent(BaseEvent):
    event_name: ClassVar[str] = "trading.position_update"
    event_version: ClassVar[int] = 1
    symbol: Symbol
    position_id: PositionId
    intent_id: IntentId
    volume: Volume
    price_open: Price
    price_current: Price
    profit: Money  # Current PnL (unrealized)
    update_epoch_ms: EpochMs
    sl: Price | None = None
    tp: Price | None = None
    app: App = App.EA_MQL5
