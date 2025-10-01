from typing import Literal

from quantum.domain.events.base import BaseEvent


class TrailingTriggerV1(BaseEvent):
    event_name: Literal["trailing_trigger_v1"] = "trailing_trigger_v1"
    app: Literal["ea_mql5"]
    symbol: str
    position_id: int
    intent_id: str | None = None
    trigger_ms: int
    price_at_trigger: float
    new_sl: float
