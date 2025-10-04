from decimal import Decimal
from typing import ClassVar

from pydantic import field_validator

from quantum.domain.events.base import BaseEvent
from quantum.domain.types.enums import App
from quantum.shared.types.time import EpochMs


class OrderFillEvent(BaseEvent):
    event_name: ClassVar[str] = "trading.order_fill"
    app: App = App.EA_MQL5
    intent_id: str
    order_id: int
    deal_id: int
    symbol: str
    price: Decimal
    volume: Decimal
    commission: Decimal
    swap: Decimal
    profit: Decimal
    reason: str  # MT5 ENUM_DEAL_REASON stringified
    fill_epoch_ms: EpochMs  # t_fill (unix ms)
    partial: bool

    @field_validator("price", "volume")
    @classmethod
    def _gt_zero(cls, v: Decimal):
        if v <= 0:
            raise ValueError("price and volume must be > 0")
        return v
