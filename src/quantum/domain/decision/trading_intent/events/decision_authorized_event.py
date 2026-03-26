from dataclasses import dataclass
from typing import ClassVar

from quantum.domain.decision.common.decision_event import DecisionEvent
from quantum.domain.shared_kernel.foundation.errors.invariants import InvariantViolation
from quantum.domain.shared_kernel.modeling.identity.intent_id import IntentId


@dataclass(frozen=True, slots=True)
class DecisionAuthorizedEvent(DecisionEvent):
    event_name: ClassVar[str] = "decision.authorized"
    event_version: ClassVar[int] = 1

    intent_id: IntentId

    def _validate_payload(self) -> None:
        if not isinstance(self.intent_id, IntentId):
            raise InvariantViolation("DecisionAuthorizedEvent.intent_id invalid")
