from dataclasses import dataclass
from typing import ClassVar

from quantum.domain.risk.attribution.risk_attribution import RiskAttribution
from quantum.domain.risk.value_objects.risk_breach import RiskBreach
from quantum.domain.shared_kernel.events.base_event import BaseEvent


@dataclass(frozen=True, slots=True)
class RiskAttributionEvent(BaseEvent):
    """
    Emitted to explicitly attribute the origin of a detected risk.
    """

    event_name: ClassVar[str] = "risk.attribution"
    event_version: ClassVar[int] = 1

    breach: RiskBreach
    attribution: RiskAttribution
