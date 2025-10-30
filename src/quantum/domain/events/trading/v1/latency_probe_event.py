from typing import ClassVar

from pydantic import computed_field, field_validator

from quantum.domain.events.base import BaseEvent
from quantum.shared.serialization.schema_registry import register_event
from quantum.shared.types.enums import App, LatencyPhase
from quantum.shared.types.value_objects import EpochMs, Symbol


@register_event
class LatencyProbeEvent(BaseEvent):
    event_name: ClassVar[str] = "trading.latency_probe"
    app: App
    phase: LatencyPhase
    symbol: Symbol
    start_epoch_ms: EpochMs
    end_epoch_ms: EpochMs

    @field_validator("end_epoch_ms")
    @classmethod
    def _end_after_start(cls, v, info):
        start = info.data.get("start_epoch_ms")
        if start is not None and v < start:
            raise ValueError("end_epoch_ms must be >= start_epoch_ms")
        return v

    @computed_field
    @property
    def duration_ms(self) -> int:
        return int(self.end_epoch_ms - self.start_epoch_ms)
