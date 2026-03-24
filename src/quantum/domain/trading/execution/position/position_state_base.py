from abc import ABC
from dataclasses import dataclass

from quantum.domain.shared_kernel.event_sourcing.events.event_sequence import (
    EventSequence,
)
from quantum.domain.shared_kernel.event_sourcing.state.aggregate_state import (
    AggregateState,
)


@dataclass(frozen=True, slots=True)
class PositionStateBase(AggregateState, ABC):

    last_sequence: EventSequence

    def last_event_sequence(self) -> EventSequence:
        return self.last_sequence
