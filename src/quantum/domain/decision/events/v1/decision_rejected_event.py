from dataclasses import dataclass
from typing import ClassVar

from quantum.domain.decision.events.decision_event import DecisionEvent
from quantum.domain.decision.governance.decision_authorization_reason_code import (
    DecisionAuthorizationReasonCode,
)
from quantum.domain.shared_kernel.modeling.identity.intent_id import IntentId


@dataclass(frozen=True, slots=True)
class DecisionRejectedEvent(DecisionEvent):
    event_name: ClassVar[str] = "decision.rejected"
    event_version: ClassVar[int] = 1

    intent_id: IntentId
    reason_code: DecisionAuthorizationReasonCode
