from dataclasses import dataclass
from typing import ClassVar

from quantum.domain.risk.boundary.decision_boundary_result import DecisionBoundaryResult
from quantum.domain.shared_kernel.events.base_event import BaseEvent
from quantum.domain.shared_kernel.identifiers.intent_id import IntentId


@dataclass(frozen=True, slots=True)
class DecisionAuthorizedEvent(BaseEvent):
    event_name: ClassVar[str] = "trading.decision.authorized"
    event_version: ClassVar[int] = 1

    intent_id: IntentId
    result: DecisionBoundaryResult
