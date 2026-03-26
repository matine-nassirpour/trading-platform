from dataclasses import dataclass
from typing import ClassVar

from quantum.domain.decision.common.decision_event import DecisionEvent
from quantum.domain.decision.common.trading_context import TradingContext
from quantum.domain.decision.qualification.decision_identity import DecisionIdentity
from quantum.domain.market.instrument.identity.symbol import Symbol
from quantum.domain.market.positioning.position_side import PositionSide
from quantum.domain.shared_kernel.foundation.errors.invariants import InvariantViolation
from quantum.domain.shared_kernel.modeling.identity.intent_id import IntentId


@dataclass(frozen=True, slots=True)
class TradingIntentCreatedEvent(DecisionEvent):
    """
    Emitted when a trading intent is created.

    This event represents the existence of a decision,
    NOT its authorization.
    """

    event_name: ClassVar[str] = "decision.trading_intent.created"
    event_version: ClassVar[int] = 1

    intent_id: IntentId
    symbol: Symbol
    side: PositionSide

    decision_identity: DecisionIdentity
    trading_context: TradingContext

    def _validate_payload(self) -> None:
        if not isinstance(self.intent_id, IntentId):
            raise InvariantViolation("TradingIntentCreatedEvent.intent_id invalid")

        if not isinstance(self.symbol, Symbol):
            raise InvariantViolation("TradingIntentCreatedEvent.symbol invalid")

        if not isinstance(self.side, PositionSide):
            raise InvariantViolation("TradingIntentCreatedEvent.side invalid")

        if not isinstance(self.decision_identity, DecisionIdentity):
            raise InvariantViolation(
                "TradingIntentCreatedEvent.decision_identity invalid"
            )

        if not isinstance(self.trading_context, TradingContext):
            raise InvariantViolation(
                "TradingIntentCreatedEvent.trading_context invalid"
            )
