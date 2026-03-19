from abc import ABC
from dataclasses import dataclass

from quantum.domain.shared_kernel.ddd.entities.aggregate_state import AggregateState
from quantum.domain.shared_kernel.event_sourcing.events.event_sequence import (
    EventSequence,
)
from quantum.domain.shared_kernel.foundation.errors.invariants import InvariantViolation


@dataclass(frozen=True, slots=True)
class CapitalReservationStateBase(AggregateState, ABC):
    """
    Algebraic base class for CapitalReservation state.

    Guarantees:
    - total state space explicitly modeled
    - fully event-sourced compatible
    """

    last_sequence: EventSequence

    def _validate(self) -> None:
        if not isinstance(self.last_sequence, EventSequence):
            raise InvariantViolation(
                "CapitalReservationStateBase.last_sequence invalid"
            )

    def last_event_sequence(self) -> EventSequence:
        return self.last_sequence
