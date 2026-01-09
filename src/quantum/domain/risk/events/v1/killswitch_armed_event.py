from dataclasses import dataclass
from typing import ClassVar

from quantum.domain.shared_kernel.events.base_event import BaseEvent


@dataclass(frozen=True)
class KillSwitchArmedEvent(BaseEvent):
    """
    Emitted when the kill switch is armed (initial or after a reset).

    This event is REQUIRED to create a valid KillSwitchState.
    """

    event_name: ClassVar[str] = "trading.killswitch_armed"
    event_version: ClassVar[int] = 1
