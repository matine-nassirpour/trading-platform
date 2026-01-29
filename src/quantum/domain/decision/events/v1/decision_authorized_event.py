from dataclasses import dataclass
from typing import ClassVar

from quantum.domain.decision.governance.decision_policy_result import (
    DecisionPolicyResult,
)
from quantum.domain.shared_kernel.events.base.decision_event import DecisionEvent
from quantum.domain.shared_kernel.identifiers.intent_id import IntentId


@dataclass(frozen=True, slots=True)
class DecisionAuthorizedEvent(DecisionEvent):
    event_name: ClassVar[str] = "trading.decision.authorized"
    event_version: ClassVar[int] = 1

    intent_id: IntentId
    result: DecisionPolicyResult
