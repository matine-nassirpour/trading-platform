from dataclasses import dataclass
from typing import ClassVar

from quantum.domain.shared_kernel.events.base_event import BaseEvent
from quantum.domain.trading.core.decision.identity.decision_identity import (
    DecisionIdentity,
)
from quantum.domain.trading.core.decision.trading_context import TradingContext
from quantum.domain.trading.value_objects.identifiers.intent_id import IntentId


@dataclass(frozen=True, slots=True)
class TradingIntentCreatedEvent(BaseEvent):
    """
    Emitted when a trading intent is created.

    This event represents the existence of a decision,
    NOT its authorization.
    """

    event_name: ClassVar[str] = "trading.intent.created"
    event_version: ClassVar[int] = 1

    intent_id: IntentId
    decision_identity: DecisionIdentity
    trading_context: TradingContext
