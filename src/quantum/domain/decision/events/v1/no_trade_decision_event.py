from dataclasses import dataclass
from typing import ClassVar

from quantum.domain.decision.events.decision_event import DecisionEvent
from quantum.domain.decision.identity.decision_identity import DecisionIdentity
from quantum.domain.decision.outcome.no_trade.no_trade_decision import NoTradeDecision
from quantum.domain.shared_kernel.value_objects.symbol import Symbol


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
