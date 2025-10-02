from decimal import Decimal
from typing import ClassVar

from pydantic import Field

from quantum.domain.events.base import BaseEvent
from quantum.domain.types.enums import App, Side
from quantum.shared.typing.time import EpochMs


class PositionUpdateEvent(BaseEvent):
    event_name: ClassVar[str] = "trading.position_update"
    app: App = App.EA_MQL5
    symbol: str
    position_id: int
    intent_id: str | None = None
    side: Side
    volume: Decimal
    price_open: Decimal
    price_current: Decimal
    sl: Decimal | None = None
    tp: Decimal | None = None
    profit: Decimal  # Current PnL (unrealized)
    update_epoch_ms: EpochMs = Field(alias="update_ms")
