from dataclasses import dataclass
from typing import ClassVar

from quantum.domain.decision.common.decision_event import DecisionEvent
from quantum.domain.decision.no_trade.no_trade_decision import NoTradeDecision
from quantum.domain.shared_kernel.foundation.errors.invariants import InvariantViolation


@dataclass(frozen=True, slots=True)
class TradingDecisionEvaluatedAsNoTradeEvent(DecisionEvent):
    """
    Emitted when a decision evaluation concludes in an explicit NO-TRADE outcome.
    """

    event_name: ClassVar[str] = "decision.trading_decision.evaluated_as_no_trade"
    event_version: ClassVar[int] = 1

    no_trade_decision: NoTradeDecision

    def _validate_payload(self) -> None:
        if not isinstance(self.no_trade_decision, NoTradeDecision):
            raise InvariantViolation(
                "TradingDecisionEvaluatedAsNoTradeEvent.no_trade_decision invalid"
            )
