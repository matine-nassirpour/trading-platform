from dataclasses import dataclass
from typing import ClassVar

from quantum.domain.shared_kernel.events.base_event import BaseEvent
from quantum.domain.shared_kernel.value_objects.symbol import Symbol
from quantum.domain.trading.core.decision.identity.decision_identity import (
    DecisionIdentity,
)
from quantum.domain.trading.value_objects.identifiers.intent_id import IntentId


@dataclass(frozen=True, slots=True)
class OrderIntentCreatedEvent(BaseEvent):
    """
    Emitted when a TradingIntent is created.

    Audit meaning:
    - A trading decision envelope was created
    - It is now a first-class governed object
    """

    event_name: ClassVar[str] = "trading.order_intent.created"
    event_version: ClassVar[int] = 1

    intent_id: IntentId
    symbol: Symbol

    decision_identity: DecisionIdentity
