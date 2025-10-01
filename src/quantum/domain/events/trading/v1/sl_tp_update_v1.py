from typing import Literal

from quantum.domain.events.base import BaseEvent


class SlTpUpdateV1(BaseEvent):
    event_name: Literal["sl_tp_update_v1"] = "sl_tp_update_v1"
    app: Literal["ea_mql5"]
    symbol: str
    position_id: int
    intent_id: str | None = None
    old_sl: float | None = None
    new_sl: float | None = None
    old_tp: float | None = None
    new_tp: float | None = None
    update_ms: int
    reason: Literal["manual", "rule", "risk"]
