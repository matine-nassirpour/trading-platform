from dataclasses import dataclass
from typing import ClassVar

from quantum.domain.events.base import BaseEvent
from quantum.domain.model.value_objects.risk_breach import RiskBreach
from quantum.domain.model.value_objects.time import EpochMs


@dataclass(frozen=True)
class RiskBreachEvent(BaseEvent):
    """
    Emitted when a configured risk limit is breached.
    """

    event_name: ClassVar[str] = "risk.breach"
    event_version: ClassVar[int] = 1

    breach: RiskBreach
    trigger_epoch_ms: EpochMs
