from __future__ import annotations

from dataclasses import dataclass

from quantum.domain.shared_kernel.foundation.errors.invariants import InvariantViolation
from quantum.domain.shared_kernel.modeling.value_objects.value_object import ValueObject


@dataclass(frozen=True, slots=True)
class EventSequence(ValueObject):
    """
    Strictly increasing, gapless event sequence.

    0 is reserved and means: 'before the first event'.
    All real events must have sequence >= 1.
    """

    value: int

    def _validate_semantics(self) -> None:
        if type(self.value) is not int:
            raise InvariantViolation("EventSequence must be a strict integer")

        if self.value < 0:
            raise InvariantViolation("EventSequence must be >= 0")

    # --- Semantics -----------------------------------------------------------

    def is_initial(self) -> bool:
        return self.value == 0

    def next(self) -> EventSequence:
        """
        Returns the next valid EventSequence.

        This is the ONLY legal way to advance a sequence.
        """
        return EventSequence(self.value + 1)

    def assert_is_next_of(self, previous: EventSequence) -> None:
        """
        Enforces strict gapless continuity:
        this == previous.next()
        """
        if not isinstance(previous, EventSequence):
            raise InvariantViolation("Previous must be an EventSequence")

        if self.value != previous.value + 1:
            raise InvariantViolation(
                f"Invalid EventSequence continuity: "
                f"expected {previous.value + 1}, got {self.value}"
            )

    @staticmethod
    def initial() -> EventSequence:
        return EventSequence(0)
