from __future__ import annotations

from dataclasses import dataclass

from quantum.domain.shared_kernel.foundation.errors.invariants import InvariantViolation
from quantum.domain.shared_kernel.modeling.temporal.epoch_ms import EpochMs
from quantum.domain.shared_kernel.modeling.value_objects.value_object import ValueObject


@dataclass(frozen=True, slots=True)
class UtcMinuteOfDay(ValueObject):
    """
    Minute index in UTC day.

    Range:
        0   -> 00:00
        1439 -> 23:59

    Guarantees:
    - Integer only
    - UTC only
    - No timezone ambiguity
    """

    value: int

    def _validate_semantics(self) -> None:
        if type(self.value) is not int:
            raise InvariantViolation("UtcMinuteOfDay must be a strict integer")

        if not 0 <= self.value <= 1439:
            raise InvariantViolation(
                "UtcMinuteOfDay must be between 0 and 1439 inclusive"
            )

    @staticmethod
    def from_epoch(epoch: EpochMs) -> UtcMinuteOfDay:
        """
        Canonical conversion from EpochMs.

        This is the ONLY allowed conversion path.
        """
        if not isinstance(epoch, EpochMs):
            raise InvariantViolation("epoch must be an EpochMs")

        return UtcMinuteOfDay(epoch.to_utc_minute_of_day())
