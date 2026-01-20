from quantum.domain.shared_kernel.value_objects.symbol import Symbol
from quantum.domain.trading.core.decision.identity.decision_identity import (
    DecisionIdentity,
)
from quantum.domain.trading.core.decision.outcome.no_trade.no_trade_decision import (
    NoTradeDecision,
)
from quantum.domain.trading.events.v1.decision.no_trade_decision_event import (
    NoTradeDecisionEvent,
)


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
