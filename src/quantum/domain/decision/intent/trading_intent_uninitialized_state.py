from dataclasses import dataclass

from quantum.domain.decision.intent.trading_intent_state_base import (
    TradingIntentStateBase,
)
from quantum.domain.shared_kernel.errors.invariants import InvariantViolation


@dataclass(frozen=True, slots=True)
class TradingIntentUninitializedState(TradingIntentStateBase):
    """
    Represents the state BEFORE TradingIntentCreatedEvent.

    This is the ONLY valid initial state.
    """

    def _validate(self) -> None:
        super()._validate()

        if not self.last_sequence.is_initial():
            raise InvariantViolation(
                "Uninitialized TradingIntent must have initial sequence"
            )
