from __future__ import annotations

from dataclasses import dataclass

from quantum.domain.shared_kernel.errors.invariants import InvariantViolation
from quantum.domain.shared_kernel.primitives.value_object import ValueObject
from quantum.domain.shared_kernel.value_objects.epoch_ms import EpochMs


@dataclass(frozen=True)
class ProjectionCursor(ValueObject):
    """
    Represents the last event position processed by a projection.

    Used for:
    - replay
    - catch-up
    - audit
    """

    last_processed_at: EpochMs

    def _validate(self) -> None:
        if not isinstance(self.last_processed_at, EpochMs):
            raise InvariantViolation("ProjectionCursor requires an EpochMs")

    @staticmethod
    def initial() -> ProjectionCursor:
        """
        Canonical initial cursor (no events processed).
        """
        return ProjectionCursor(last_processed_at=EpochMs(0))
