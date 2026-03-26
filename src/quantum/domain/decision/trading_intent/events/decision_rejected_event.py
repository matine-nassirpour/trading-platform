from dataclasses import dataclass
from typing import ClassVar

from quantum.domain.decision.authorization.decision_authorization_reason_code import (
    DecisionAuthorizationReasonCode,
)
from quantum.domain.decision.common.decision_event import DecisionEvent
from quantum.domain.shared_kernel.foundation.errors.invariants import InvariantViolation
from quantum.domain.shared_kernel.modeling.identity.intent_id import IntentId


@dataclass(frozen=True, slots=True)
class DecisionRejectedEvent(DecisionEvent):
    event_name: ClassVar[str] = "decision.rejected"
    event_version: ClassVar[int] = 1

    intent_id: IntentId
    reason_code: DecisionAuthorizationReasonCode

    def _validate_payload(self) -> None:
        if not isinstance(self.intent_id, IntentId):
            raise InvariantViolation("DecisionRejectedEvent.intent_id invalid")

        if not isinstance(self.reason_code, DecisionAuthorizationReasonCode):
            raise InvariantViolation("DecisionRejectedEvent.reason_code invalid")
