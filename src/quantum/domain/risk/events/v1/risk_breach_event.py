from dataclasses import dataclass
from typing import ClassVar

from quantum.domain.risk.value_objects.risk_breach import RiskBreach
from quantum.domain.shared.events.base_event import BaseEvent
from quantum.domain.shared.value_objects.epoch_ms import EpochMs


@dataclass(frozen=True)
class RiskBreachEvent(BaseEvent):
    """
    Emitted when a configured risk limit is breached.
    """

    event_name: ClassVar[str] = "risk.breach"
    event_version: ClassVar[int] = 1

    breach: RiskBreach
    trigger_epoch_ms: EpochMs
