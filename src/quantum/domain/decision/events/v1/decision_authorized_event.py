from dataclasses import dataclass
from typing import ClassVar

from quantum.domain.decision.identity.decision_identity import DecisionIdentity
from quantum.domain.shared_kernel.events.base.decision_event import DecisionEvent
from quantum.domain.shared_kernel.identifiers.intent_id import IntentId
from quantum.domain.shared_kernel.value_objects.epoch_ms import EpochMs


@dataclass(frozen=True, slots=True)
class DecisionAuthorizedEvent(DecisionEvent):
    event_name: ClassVar[str] = "trading.decision.authorized"
    event_version: ClassVar[int] = 1

    intent_id: IntentId
    decision_identity: DecisionIdentity

    authorized_at: EpochMs
