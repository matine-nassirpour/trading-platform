from __future__ import annotations

from dataclasses import dataclass

from quantum.domain.shared_kernel.event_sourcing.events.event_id import EventId
from quantum.domain.shared_kernel.event_sourcing.events.event_sequence import (
    EventSequence,
)
from quantum.domain.shared_kernel.event_sourcing.projections.cursor import Cursor
from quantum.domain.shared_kernel.foundation.errors.invariants import InvariantViolation


@dataclass(frozen=True, slots=True)
class ProjectionCursor(Cursor):
    """
    Strong projection cursor.

    Represents exactly the last processed event in a projection.
    """

    last_event_id: EventId
    last_sequence: EventSequence

    # --- Invariants -----------------------------------------------------------

    def _validate_semantics(self) -> None:
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
