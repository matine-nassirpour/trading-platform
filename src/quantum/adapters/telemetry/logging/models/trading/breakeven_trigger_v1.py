from typing import Literal

from quantum.adapters.telemetry.logging.models.trading.base import BaseEvent


class BreakevenTriggerV1(BaseEvent):
    event_name: Literal["breakeven_trigger_v1"] = "breakeven_trigger_v1"
    app: Literal["ea_mql5"]
    symbol: str
    position_id: int
    intent_id: str | None = None
    trigger_ms: int
    price_at_trigger: float
