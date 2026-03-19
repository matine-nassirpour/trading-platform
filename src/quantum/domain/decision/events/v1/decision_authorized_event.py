from dataclasses import dataclass
from typing import ClassVar

from quantum.domain.decision.events.decision_event import DecisionEvent
from quantum.domain.shared_kernel.identity.intent_id import IntentId


@dataclass(frozen=True, slots=True)
class DecisionAuthorizedEvent(DecisionEvent):
    event_name: ClassVar[str] = "decision.authorized"
    event_version: ClassVar[int] = 1

    intent_id: IntentId
