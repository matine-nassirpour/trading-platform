from dataclasses import dataclass
from typing import ClassVar

from quantum.domain.safety_control.events.safety_event import SafetyEvent


@dataclass(frozen=True, slots=True)
class KillSwitchArmedEvent(SafetyEvent):
    """
    Emitted when the kill switch is armed.
    """

    event_name: ClassVar[str] = "risk.killswitch.armed"
    event_version: ClassVar[int] = 1
