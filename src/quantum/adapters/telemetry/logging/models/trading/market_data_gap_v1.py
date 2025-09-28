from typing import Literal

from quantum.adapters.telemetry.logging.models.trading.base import BaseEvent


class MarketDataGapV1(BaseEvent):
    event_name: Literal["market_data_gap_v1"] = "market_data_gap_v1"
    app: Literal["ea_mql5"]
    symbol: str
    gap_ms: int  # staleness detected
    last_tick_ms: int
    now_ms: int
