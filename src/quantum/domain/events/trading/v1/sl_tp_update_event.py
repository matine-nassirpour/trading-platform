from typing import ClassVar, Literal

from quantum.domain.events.base import BaseEvent
from quantum.domain.types.enums import App


class SlTpUpdateEvent(BaseEvent):
    event_name: ClassVar[str] = "trading.sl_tp_update"
    app: App = App.EA_MQL5
    symbol: str
    position_id: int
    intent_id: str | None = None
    old_sl: float | None = None
    new_sl: float | None = None
    old_tp: float | None = None
    new_tp: float | None = None
    update_ms: int
    reason: Literal["manual", "rule", "risk"]
