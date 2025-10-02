from typing import ClassVar

from quantum.domain.events.base import BaseEvent
from quantum.domain.types.enums import App


class MarketDataGapEvent(BaseEvent):
    event_name: ClassVar[str] = "trading.market_data_gap"
    app: App = App.EA_MQL5
    symbol: str
    gap_ms: int  # staleness detected
    last_tick_ms: int
    now_ms: int
