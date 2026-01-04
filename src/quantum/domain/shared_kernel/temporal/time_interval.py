from __future__ import annotations

from dataclasses import dataclass

from quantum.domain.shared_kernel.errors.invariants import InvariantViolation
from quantum.domain.shared_kernel.primitives.value_object import ValueObject
from quantum.domain.shared_kernel.value_objects.epoch_ms import EpochMs


@dataclass(frozen=True)
class TimeInterval(ValueObject):
    """
    Canonical closed-open time interval [valid_from, valid_until).

    Semantics:
    - valid_from is inclusive
    - valid_until is exclusive
    - valid_until = None means open-ended
    """

    valid_from: EpochMs
    valid_until: EpochMs | None = None

    def _validate(self) -> None:
        if not isinstance(self.valid_from, EpochMs):
            raise InvariantViolation("valid_from must be an EpochMs")

        if self.valid_until is not None:
            if not isinstance(self.valid_until, EpochMs):
                raise InvariantViolation("valid_until must be an EpochMs")

            if self.valid_until.value <= self.valid_from.value:
                raise InvariantViolation(
                    "valid_until must be strictly greater than valid_from"
                )

    # --- Semantics ------------------------------------------------------------

    def contains(self, instant: EpochMs) -> bool:
        if instant.value < self.valid_from.value:
            return False

        if self.valid_until is not None:
            return instant.value < self.valid_until.value

        return True

    def is_open_ended(self) -> bool:
        return self.valid_until is None

    def close(self, *, at: EpochMs) -> TimeInterval:
        """
        Returns a new interval closed at the given instant.
        """
        if at.value <= self.valid_from.value:
            raise InvariantViolation("Cannot close interval before it starts")

        if self.valid_until is not None:
            raise InvariantViolation("Interval already closed")

        return TimeInterval(
            valid_from=self.valid_from,
            valid_until=at,
        )
