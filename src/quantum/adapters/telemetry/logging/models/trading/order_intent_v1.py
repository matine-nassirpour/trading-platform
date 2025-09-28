from typing import Literal

from pydantic import BaseModel


class TradeIntentV1(BaseModel):
    event_name: Literal["trade_intent_v1"] = "trade_intent_v1"
    app: Literal["python_core", "ea_mql5"]
    intent_id: str
    symbol: str
    side: Literal["buy", "sell"]
    type: Literal["market", "limit", "stop", "stop_limit"]
    volume: float
    price: float | None = None
    sl: float | None = None
    tp: float | None = None
    time_in_force: Literal["ioc", "fok", "gtc"] | None = "gtc"
    client_order_id: str | None = None
    rationale: str | None = None  # brief tag “setup”
