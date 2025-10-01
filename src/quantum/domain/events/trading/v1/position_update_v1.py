from typing import Literal

from quantum.domain.events.base import BaseEvent


class PositionUpdateV1(BaseEvent):
    event_name: Literal["position_update_v1"] = "position_update_v1"
    app: Literal["ea_mql5"]
    symbol: str
    position_id: int
    intent_id: str | None = None
    side: Literal["long", "short", "flat"]
    volume: float
    price_open: float
    price_current: float
    sl: float | None = None
    tp: float | None = None
    profit: float  # current (unrealized)
    update_ms: int
