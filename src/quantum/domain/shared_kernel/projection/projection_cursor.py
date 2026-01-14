from __future__ import annotations

from dataclasses import dataclass

from quantum.domain.shared_kernel.errors.invariants import InvariantViolation
from quantum.domain.shared_kernel.events.event_id import EventId
from quantum.domain.shared_kernel.events.event_sequence import EventSequence
from quantum.domain.shared_kernel.primitives.cursor import Cursor


@dataclass(frozen=True, slots=True)
class ProjectionCursor(Cursor):
    """
    Strong projection cursor.

    Represents exactly the last processed event in a projection.
    """

    last_event_id: EventId
    last_sequence: EventSequence

    # --- Invariants -----------------------------------------------------------

    def _validate(self) -> None:
        if not isinstance(self.last_event_id, EventId):
            raise InvariantViolation("ProjectionCursor requires EventId")

        if not isinstance(self.last_sequence, EventSequence):
            raise InvariantViolation("ProjectionCursor requires EventSequence")

    # --- Constructors --------------------------------------------------------

    @staticmethod
    def initial() -> ProjectionCursor:
        return ProjectionCursor(
            last_event_id=EventId.nil(),
            last_sequence=EventSequence.initial(),
        )
