from dataclasses import dataclass
from typing import ClassVar

from quantum.domain.shared_kernel.events.base.risk_event import RiskEvent


@dataclass(frozen=True, slots=True)
class KillSwitchArmedEvent(RiskEvent):
    """
    Emitted when the kill switch is armed.
    """

    event_name: ClassVar[str] = "risk.killswitch.armed"
    event_version: ClassVar[int] = 1
