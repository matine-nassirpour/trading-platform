from dataclasses import dataclass
from typing import ClassVar

from quantum.domain.decision.common.decision_event import DecisionEvent
from quantum.domain.decision.no_trade.no_trade_decision import NoTradeDecision
from quantum.domain.decision.qualification.decision_identity import DecisionIdentity
from quantum.domain.market.instrument.identity.symbol import Symbol
from quantum.domain.shared_kernel.foundation.errors.invariants import InvariantViolation


@dataclass(frozen=True, slots=True)
class NoTradeDecisionEvent(DecisionEvent):
    """
    Emitted when a trading decision results in an explicit NO-TRADE outcome.

    This event is a FIRST-CLASS DECISION ARTIFACT.

    Audit meaning:
    - A decision was evaluated
    - It was VALID
    - It resulted in an intentional abstention
    """

    event_name: ClassVar[str] = "decision.no_trade"
    event_version: ClassVar[int] = 1

    symbol: Symbol
    decision_identity: DecisionIdentity
    no_trade_decision: NoTradeDecision

    def _validate_payload(self) -> None:
        if not isinstance(self.symbol, Symbol):
            raise InvariantViolation("NoTradeDecisionEvent.intent_id invalid")

        if not isinstance(self.decision_identity, DecisionIdentity):
            raise InvariantViolation("NoTradeDecisionEvent.reason_code invalid")

        if not isinstance(self.no_trade_decision, NoTradeDecision):
            raise InvariantViolation("NoTradeDecisionEvent.reason_code invalid")
