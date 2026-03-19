from abc import ABC
from dataclasses import dataclass

from quantum.domain.shared_kernel.ddd.entities.aggregate_state import AggregateState
from quantum.domain.shared_kernel.event_sourcing.events.event_sequence import (
    EventSequence,
)


@dataclass(frozen=True, slots=True)
class PositionStateBase(AggregateState, ABC):

    last_sequence: EventSequence

    def last_event_sequence(self) -> EventSequence:
        return self.last_sequence
