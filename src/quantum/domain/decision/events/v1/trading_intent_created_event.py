from dataclasses import dataclass
from typing import ClassVar

from quantum.domain.decision.context.trading_context import TradingContext
from quantum.domain.decision.identity.decision_identity import DecisionIdentity
from quantum.domain.shared_kernel.events.base.fact_event import FactEvent
from quantum.domain.shared_kernel.identifiers.intent_id import IntentId
from quantum.domain.shared_kernel.value_objects.position_side import PositionSide
from quantum.domain.shared_kernel.value_objects.symbol import Symbol


@dataclass(frozen=True, slots=True)
class TradingIntentCreatedEvent(FactEvent):
    """
    Emitted when a trading intent is created.

    This event represents the existence of a decision,
    NOT its authorization.
    """

    event_name: ClassVar[str] = "trading.intent.created"
    event_version: ClassVar[int] = 1

    intent_id: IntentId
    symbol: Symbol
    side: PositionSide

    decision_identity: DecisionIdentity
    trading_context: TradingContext
