from typing import ClassVar

from quantum.domain.events.base import BaseEvent
from quantum.domain.model.value_objects.symbol import Symbol
from quantum.domain.model.value_objects.time import EpochMs
from quantum.domain.types.enums import App, LatencyPhase


class LatencyProbeEvent(BaseEvent):
    event_name: ClassVar[str] = "trading.latency_probe"
    app: App
    phase: LatencyPhase
    symbol: Symbol
    start_epoch_ms: EpochMs
    end_epoch_ms: EpochMs
