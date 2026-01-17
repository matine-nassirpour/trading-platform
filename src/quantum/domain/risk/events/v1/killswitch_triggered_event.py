from dataclasses import dataclass
from typing import ClassVar

from quantum.domain.risk.governance.aggregates.kill_switch.reason import (
    KillSwitchReason,
)
from quantum.domain.shared_kernel.events.base_event import BaseEvent


@dataclass(frozen=True, slots=True)
class KillSwitchTriggeredEvent(BaseEvent):
    event_name: ClassVar[str] = "trading.killswitch_trigger"
    event_version: ClassVar[int] = 1

    reason: KillSwitchReason
    detail: str | None = None
