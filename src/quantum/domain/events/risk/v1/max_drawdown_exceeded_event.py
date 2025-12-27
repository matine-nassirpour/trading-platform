from dataclasses import dataclass
from typing import ClassVar

from quantum.domain.events.base import BaseEvent
from quantum.domain.model.value_objects.money import Money
from quantum.domain.model.value_objects.time import EpochMs


@dataclass(frozen=True)
class MaxDrawdownExceededEvent(BaseEvent):
    event_name: ClassVar[str] = "risk.max_drawdown_exceeded"

    current_drawdown: Money
    limit: Money
    trigger_epoch_ms: EpochMs
