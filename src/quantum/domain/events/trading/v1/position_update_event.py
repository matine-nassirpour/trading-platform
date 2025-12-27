from dataclasses import dataclass
from decimal import Decimal
from typing import ClassVar

from quantum.domain.events.base import BaseEvent
from quantum.domain.model.value_objects.identifiers import IntentId, PositionId
from quantum.domain.model.value_objects.symbol import Symbol
from quantum.domain.model.value_objects.time import EpochMs
from quantum.domain.types.enums import App


@dataclass(frozen=True)
class PositionUpdateEvent(BaseEvent):
    event_name: ClassVar[str] = "trading.position_update"
    symbol: Symbol
    position_id: PositionId
    intent_id: IntentId
    volume: Decimal
    price_open: Decimal
    price_current: Decimal
    profit: Decimal  # Current PnL (unrealized)
    update_epoch_ms: EpochMs
    sl: Decimal | None = None
    tp: Decimal | None = None
    app: App = App.EA_MQL5
