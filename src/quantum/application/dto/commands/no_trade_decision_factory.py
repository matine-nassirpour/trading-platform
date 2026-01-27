from quantum.domain.decision.events.v1.no_trade_decision_event import (
    NoTradeDecisionEvent,
)
from quantum.domain.decision.identity.decision_identity import DecisionIdentity
from quantum.domain.decision.outcome.no_trade.no_trade_decision import NoTradeDecision
from quantum.domain.shared_kernel.value_objects.symbol import Symbol


class NoTradeDecisionFactory:
    """
    Canonical factory for NoTradeDecisionEvent.
    """

    @staticmethod
    def create(
        *,
        symbol: Symbol,
        decision_identity: DecisionIdentity,
        decision: NoTradeDecision,
    ) -> NoTradeDecisionEvent:
        return NoTradeDecisionEvent(
            symbol=symbol,
            decision_identity=decision_identity,
            no_trade_decision=decision,
        )
