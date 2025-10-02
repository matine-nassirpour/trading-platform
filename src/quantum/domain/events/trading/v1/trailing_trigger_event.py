from decimal import Decimal
from typing import ClassVar

from quantum.domain.events.base import BaseEvent
from quantum.domain.types.enums import App
from quantum.shared.typing.time import EpochMs


class TrailingTriggerEvent(BaseEvent):
    event_name: ClassVar[str] = "trading.trailing_trigger"
    app: App = App.EA_MQL5
    symbol: str
    position_id: int
    intent_id: str | None = None
    trigger_epoch_ms: EpochMs
    price_at_trigger: Decimal
    new_sl: Decimal
