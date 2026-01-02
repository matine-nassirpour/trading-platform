from dataclasses import dataclass
from typing import ClassVar

from quantum.domain.risk.attribution.risk_attribution import RiskAttribution
from quantum.domain.risk.value_objects.risk_breach_kind import RiskBreachKind
from quantum.domain.shared.events.base_event import BaseEvent
from quantum.domain.shared.value_objects.epoch_ms import EpochMs


@dataclass(frozen=True)
class RiskAttributionEvent(BaseEvent):
    """
    Emitted to explicitly attribute the origin of a detected risk.
    """

    event_name: ClassVar[str] = "risk.attribution"
    event_version: ClassVar[int] = 1

    breach_kind: RiskBreachKind
    attribution: RiskAttribution

    trigger_epoch_ms: EpochMs
