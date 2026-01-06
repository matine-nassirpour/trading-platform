from dataclasses import dataclass
from typing import ClassVar

from quantum.domain.shared_kernel.events.base_event import BaseEvent
from quantum.domain.trading.decision.governance.boundary.decision_boundary_result import (
    DecisionBoundaryResult,
)
from quantum.domain.trading.value_objects.identifiers.intent_id import IntentId


@dataclass(frozen=True)
class DecisionAuthorizedEvent(BaseEvent):
    """
    Emitted when a trading decision is evaluated against a DecisionBoundary.
    """

    event_name: ClassVar[str] = "trading.decision_authorized"
    event_version: ClassVar[int] = 1

    intent_id: IntentId
    result: DecisionBoundaryResult
