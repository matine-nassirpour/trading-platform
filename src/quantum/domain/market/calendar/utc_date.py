from __future__ import annotations

import calendar

from dataclasses import dataclass

from quantum.domain.shared_kernel.foundation.errors.invariants import InvariantViolation
from quantum.domain.shared_kernel.modeling.temporal.epoch_ms import EpochMs
from quantum.domain.shared_kernel.modeling.value_objects.value_object import ValueObject


@dataclass(frozen=True, slots=True)
class UtcDate(ValueObject):
    """
    Canonical UTC calendar date.

    Format:
        YYYY-MM-DD

    Guarantees:
    - explicit domain date representation
    - UTC-derived only when constructed from EpochMs
    - no datetime.date inside canonical domain state
    - deterministic serialization
    """

    year: int
    month: int
    day: int

    def _validate_semantics(self) -> None:
        if type(self.year) is not int:
            raise InvariantViolation("UtcDate.year must be a strict integer")

        if type(self.month) is not int:
            raise InvariantViolation("UtcDate.month must be a strict integer")

        if type(self.day) is not int:
            raise InvariantViolation("UtcDate.day must be a strict integer")

        if not 1970 <= self.year <= 9999:
            raise InvariantViolation("UtcDate.year must be in range [1970..9999]")

        if not 1 <= self.month <= 12:
            raise InvariantViolation("UtcDate.month must be in range [1..12]")

        max_day = calendar.monthrange(self.year, self.month)[1]

        if not 1 <= self.day <= max_day:
            raise InvariantViolation(
                f"UtcDate.day must be in range [1..{max_day}] "
                f"for {self.year:04d}-{self.month:02d}"
            )

    @staticmethod
    def from_epoch(epoch: EpochMs) -> UtcDate:
        if not isinstance(epoch, EpochMs):
            raise InvariantViolation("epoch must be an EpochMs")

        dt = epoch.to_datetime()

        return UtcDate(
            year=dt.year,
            month=dt.month,
            day=dt.day,
        )

    def weekday(self) -> int:
        """
        Returns ISO-compatible weekday index:
        Monday = 0, Sunday = 6.
        """
        return calendar.weekday(self.year, self.month, self.day)

    def __str__(self) -> str:
        return f"{self.year:04d}-{self.month:02d}-{self.day:02d}"
