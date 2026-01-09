from __future__ import annotations

from dataclasses import dataclass

from quantum.domain.shared_kernel.errors.invariants import InvariantViolation
from quantum.domain.shared_kernel.events.event_id import EventId
from quantum.domain.shared_kernel.events.event_sequence import EventSequence
from quantum.domain.shared_kernel.primitives.value_object import ValueObject


@dataclass(frozen=True)
class ProjectionCursor(ValueObject):
    """
    Strong projection cursor.

    Represents exactly the last processed event.
    """

    last_event_id: EventId
    last_sequence: EventSequence | None

    def _validate(self) -> None:
        if self.last_sequence is not None and not isinstance(
            self.last_sequence, EventSequence
        ):
            raise InvariantViolation("Cursor requires EventSequence or None")

    @staticmethod
    def initial() -> ProjectionCursor:
        return ProjectionCursor(
            last_event_id=EventId.new(),
            last_sequence=None,
        )
