from __future__ import annotations

from dataclasses import dataclass

from quantum.domain.shared_kernel.errors.invariants import InvariantViolation
from quantum.domain.shared_kernel.primitives.value_object import ValueObject


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

    def _validate(self) -> None:
        if not isinstance(self.value, int):
            raise InvariantViolation("UtcMinuteOfDay must be an integer")

        if not 0 <= self.value <= 1439:
            raise InvariantViolation(
                "UtcMinuteOfDay must be between 0 and 1439 inclusive"
            )

    @staticmethod
    def from_epoch_ms(epoch_ms: int) -> UtcMinuteOfDay:
        """
        Converts epoch milliseconds to UTC minute-of-day.
        """
        if not isinstance(epoch_ms, int):
            raise InvariantViolation("epoch_ms must be an integer")

        seconds = (epoch_ms // 1000) % 86400
        minute = seconds // 60
        return UtcMinuteOfDay(minute)
