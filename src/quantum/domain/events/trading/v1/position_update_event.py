from decimal import Decimal
from typing import ClassVar

from pydantic import field_validator

from quantum.shared.events.base import BaseEvent
from quantum.shared.serialization.schema_registry import register_event
from quantum.shared.types.decimal_validators import PositiveDecimal
from quantum.shared.types.enums import App
from quantum.shared.types.value_objects import EpochMs, IntentId, PositionId, Symbol


@register_event
class PositionUpdateEvent(BaseEvent):
    event_name: ClassVar[str] = "trading.position_update"
    app: App = App.EA_MQL5
    symbol: Symbol
    position_id: PositionId
    intent_id: IntentId | None = None
    volume: PositiveDecimal
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
