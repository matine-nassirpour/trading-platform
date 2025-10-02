from typing import ClassVar

from quantum.domain.events.base import BaseEvent
from quantum.domain.types.enums import App, LatencyPhase


class LatencyProbeEvent(BaseEvent):
    event_name: ClassVar[str] = "trading.latency_probe"
    app: App
    phase: LatencyPhase
    symbol: str
    start_ms: int
    end_ms: int
