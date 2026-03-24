from __future__ import annotations

from dataclasses import dataclass

from quantum.domain.shared_kernel.foundation.errors.invariants import InvariantViolation
from quantum.domain.shared_kernel.modeling.temporal.epoch_ms import EpochMs
from quantum.domain.shared_kernel.modeling.temporal.time_interval import TimeInterval
from quantum.domain.shared_kernel.modeling.value_objects.value_object import ValueObject


@dataclass(frozen=True, slots=True)
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
