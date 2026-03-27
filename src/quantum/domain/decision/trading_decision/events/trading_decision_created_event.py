from dataclasses import dataclass
from typing import ClassVar

from quantum.domain.decision.common.decision_event import DecisionEvent
from quantum.domain.decision.common.trading_context import TradingContext
from quantum.domain.decision.qualification.decision_identity import DecisionIdentity
from quantum.domain.market.instrument.identity.symbol import Symbol
from quantum.domain.shared_kernel.foundation.errors.invariants import InvariantViolation


@dataclass(frozen=True, slots=True)
class TradingDecisionCreatedEvent(DecisionEvent):
    """
    Emitted when a trading decision evaluation context is created.

    IMPORTANT:
    - stream identity is carried by the recorded event envelope
    - this event does NOT declare a trade intent yet
    """

    event_name: ClassVar[str] = "decision.trading_decision.created"
    event_version: ClassVar[int] = 1

    symbol: Symbol
    decision_identity: DecisionIdentity
    trading_context: TradingContext

    def _validate_payload(self) -> None:
        if not isinstance(self.symbol, Symbol):
            raise InvariantViolation("TradingDecisionCreatedEvent.symbol invalid")

        if not isinstance(self.decision_identity, DecisionIdentity):
            raise InvariantViolation(
                "TradingDecisionCreatedEvent.decision_identity invalid"
            )

        if not isinstance(self.trading_context, TradingContext):
            raise InvariantViolation(
                "TradingDecisionCreatedEvent.trading_context invalid"
            )
