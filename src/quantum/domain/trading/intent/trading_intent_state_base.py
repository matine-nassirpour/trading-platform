from abc import ABC
from dataclasses import dataclass

from quantum.domain.shared_kernel.events.event_sequence import EventSequence
from quantum.domain.shared_kernel.primitives.aggregate_state import AggregateState


@dataclass(frozen=True, slots=True)
class TradingIntentStateBase(AggregateState, ABC):
    """
    Algebraic base class for TradingIntent state.

    Guarantees:

    - Total state space explicitly modeled
    - No implicit or None states
    - Fully event-sourced compatible
    """

    last_sequence: EventSequence

    def last_event_sequence(self) -> EventSequence:
        return self.last_sequence
