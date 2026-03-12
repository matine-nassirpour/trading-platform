from abc import ABC
from dataclasses import dataclass

from quantum.domain.shared_kernel.errors.invariants import InvariantViolation
from quantum.domain.shared_kernel.events.event_sequence import EventSequence
from quantum.domain.shared_kernel.primitives.aggregate_state import AggregateState


@dataclass(frozen=True, slots=True)
class OrderStateBase(AggregateState, ABC):
    """
    Common immutable base state for the Order aggregate.

    `last_sequence` is the canonical state-carried version marker.
    """

    last_sequence: EventSequence

    def _validate(self) -> None:
        if not isinstance(self.last_sequence, EventSequence):
            raise InvariantViolation("OrderStateBase.last_sequence invalid")

    def last_event_sequence(self) -> EventSequence:
        """
        Canonical aggregate version carried by the order state.
        """
        return self.last_sequence
