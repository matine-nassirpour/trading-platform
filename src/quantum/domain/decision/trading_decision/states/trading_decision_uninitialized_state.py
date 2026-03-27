from dataclasses import dataclass

from quantum.domain.decision.trading_decision.states.trading_decision_state_base import (
    TradingDecisionStateBase,
)
from quantum.domain.shared_kernel.foundation.errors.invariants import InvariantViolation


@dataclass(frozen=True, slots=True)
class TradingDecisionUninitializedState(TradingDecisionStateBase):
    """
    Represents the state before TradingDecisionCreatedEvent.
    """

    def _validate_semantics(self) -> None:
        super()._validate_semantics()

        if not self.last_sequence.is_initial():
            raise InvariantViolation(
                "Uninitialized TradingDecision must have initial sequence"
            )
