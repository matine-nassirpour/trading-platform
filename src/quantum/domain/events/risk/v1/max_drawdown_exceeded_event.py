from dataclasses import dataclass
from typing import ClassVar

from quantum.domain.events.base import BaseEvent
from quantum.domain.model.value_objects.drawdown import Drawdown
from quantum.domain.model.value_objects.money import Money
from quantum.domain.model.value_objects.time import EpochMs


@dataclass(frozen=True)
class MaxDrawdownExceededEvent(BaseEvent):
    """
    Emitted when the drawdown exceeds or equals the configured maximum.

    Convention:
    - drawdown is ALWAYS positive (peak - equity)
    """

    event_name: ClassVar[str] = "risk.max_drawdown_exceeded"
    event_version: ClassVar[int] = 1

    current_drawdown: Drawdown
    limit: Money
    trigger_epoch_ms: EpochMs
