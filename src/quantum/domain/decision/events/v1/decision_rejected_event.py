from dataclasses import dataclass
from typing import ClassVar

from quantum.domain.decision.governance.decision_authorization_reason_code import (
    DecisionAuthorizationReasonCode,
)
from quantum.domain.decision.identity.decision_identity import DecisionIdentity
from quantum.domain.shared_kernel.events.base.decision_event import DecisionEvent
from quantum.domain.shared_kernel.identifiers.intent_id import IntentId
from quantum.domain.shared_kernel.value_objects.epoch_ms import EpochMs


@dataclass(frozen=True, slots=True)
class DecisionRejectedEvent(DecisionEvent):
    event_name: ClassVar[str] = "trading.decision.rejected"
    event_version: ClassVar[int] = 1

    intent_id: IntentId
    decision_identity: DecisionIdentity

    rejected_at: EpochMs
    reason_code: DecisionAuthorizationReasonCode
