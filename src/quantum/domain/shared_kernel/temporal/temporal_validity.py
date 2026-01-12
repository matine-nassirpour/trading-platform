from __future__ import annotations

from dataclasses import dataclass

from quantum.domain.shared_kernel.errors.invariants import InvariantViolation
from quantum.domain.shared_kernel.primitives.value_object import ValueObject
from quantum.domain.shared_kernel.temporal.time_interval import TimeInterval
from quantum.domain.shared_kernel.value_objects.epoch_ms import EpochMs


@dataclass(frozen=True)
class TemporalValidity(ValueObject):
    """
    Canonical temporal validity contract.

    Used to express WHEN a domain concept is applicable.
    """

    interval: TimeInterval

    def _validate_semantics(self) -> None:
        if not isinstance(self.interval, TimeInterval):
            raise InvariantViolation("TemporalValidity requires a TimeInterval")

    # --- Semantics ------------------------------------------------------------

    def is_valid_at(self, at: EpochMs) -> bool:
        return self.interval.contains(at)

    def close(self, *, at: EpochMs) -> TemporalValidity:
        return TemporalValidity(interval=self.interval.close(at=at))

    @staticmethod
    def starting_now(at: EpochMs) -> TemporalValidity:
        return TemporalValidity(interval=TimeInterval(valid_from=at))
