from decimal import Decimal
from typing import ClassVar

from pydantic import field_validator

from quantum.domain.events.base import BaseEvent
from quantum.domain.types.enums import App, PositionSide
from quantum.shared.types.time import EpochMs


class PositionUpdateEvent(BaseEvent):
    event_name: ClassVar[str] = "trading.position_update"
    app: App = App.EA_MQL5
    symbol: str
    position_id: int
    intent_id: str | None = None
    side: PositionSide
    volume: Decimal
    price_open: Decimal
    price_current: Decimal
    sl: Decimal | None = None
    tp: Decimal | None = None
    profit: Decimal  # Current PnL (unrealized)
    update_epoch_ms: EpochMs

    @field_validator("volume")
    @classmethod
    def _volume_non_negative(cls, v: Decimal):
        if v < 0:
            raise ValueError("volume must be >= 0")
        return v
