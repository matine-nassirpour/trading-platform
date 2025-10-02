from typing import ClassVar

from quantum.domain.events.base import BaseEvent
from quantum.domain.types.enums import App


class TrailingTriggerEvent(BaseEvent):
    event_name: ClassVar[str] = "trading.trailing_trigger"
    app: App = App.EA_MQL5
    symbol: str
    position_id: int
    intent_id: str | None = None
    trigger_ms: int
    price_at_trigger: float
    new_sl: float
