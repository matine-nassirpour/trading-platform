from __future__ import annotations

from quantum.domain.shared_kernel.architecture.domain_charter import DomainRole
from quantum.domain.shared_kernel.architecture.immutable_dataclass import (
    immutable_dataclass,
)
from quantum.domain.shared_kernel.errors.invariants import InvariantViolation
from quantum.domain.shared_kernel.primitives.mutation_key import MutationKey
from quantum.domain.shared_kernel.primitives.value_object import ValueObject
from quantum.domain.shared_kernel.temporal.time_interval import TimeInterval
from quantum.domain.shared_kernel.value_objects.epoch_ms import EpochMs


@immutable_dataclass
class TemporalValidity(ValueObject):
    """
    Canonical temporal validity contract.

    Used to express WHEN a domain concept is applicable.
    """

    interval: TimeInterval

    @classmethod
    def role(cls) -> DomainRole:
        return DomainRole.VALUE_OBJECT

    def _validate_semantics(self, key: MutationKey) -> None:
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
