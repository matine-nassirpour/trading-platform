from __future__ import annotations

from dataclasses import dataclass

from quantum.domain.shared_kernel.errors.invariants import InvariantViolation


@dataclass(frozen=True)
class EventSequence:
    """
    Strictly increasing, gapless sequence number within an event stream.

    Sequence 0 is RESERVED and means: 'before the first event'.
    """

    value: int

    def __post_init__(self) -> None:
        if not isinstance(self.value, int):
            raise InvariantViolation("EventSequence must be an integer")

        if self.value < 0:
            raise InvariantViolation("EventSequence must be >= 0")

    @staticmethod
    def initial() -> EventSequence:
        return EventSequence(0)
