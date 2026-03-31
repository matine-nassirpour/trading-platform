from dataclasses import dataclass
from typing import ClassVar

from quantum.domain.decision.common.decision_event import DecisionEvent
from quantum.domain.decision.trading_decision.trade_direction import TradeDirection
from quantum.domain.shared_kernel.foundation.errors.invariants import InvariantViolation


@dataclass(frozen=True, slots=True)
class TradingDecisionEvaluatedAsTradeCandidateEvent(DecisionEvent):
    """
    Emitted when a decision evaluation concludes that a trade candidate exists.
    """

    event_name: ClassVar[str] = "decision.trading_decision.evaluated_as_trade_candidate"
    event_version: ClassVar[int] = 1

    trade_direction: TradeDirection

    def _validate_payload(self) -> None:
        if not isinstance(self.trade_direction, TradeDirection):
            raise InvariantViolation(
                "TradingDecisionEvaluatedAsTradeCandidateEvent.trade_direction invalid"
            )
