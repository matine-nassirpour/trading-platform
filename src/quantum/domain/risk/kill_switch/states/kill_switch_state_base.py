from abc import ABC
from dataclasses import dataclass

from quantum.domain.shared_kernel.event_sourcing.events.event_sequence import (
    EventSequence,
)
from quantum.domain.shared_kernel.event_sourcing.state.aggregate_state import (
    AggregateState,
)
from quantum.domain.shared_kernel.foundation.errors.invariants import InvariantViolation


@dataclass(frozen=True, slots=True)
class KillSwitchStateBase(AggregateState, ABC):

    last_sequence: EventSequence

    def _validate_semantics(self) -> None:
        if not isinstance(self.last_sequence, EventSequence):
            raise InvariantViolation("KillSwitchStateBase.last_sequence invalid")

    def last_event_sequence(self) -> EventSequence:
        return self.last_sequence
