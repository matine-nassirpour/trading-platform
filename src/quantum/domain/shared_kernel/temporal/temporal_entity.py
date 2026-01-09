from __future__ import annotations

from abc import ABC
from dataclasses import dataclass, replace

from quantum.domain.shared_kernel.architecture.domain_object import DomainObject
from quantum.domain.shared_kernel.errors.invariants import InvariantViolation
from quantum.domain.shared_kernel.temporal.temporal_validity import TemporalValidity
from quantum.domain.shared_kernel.value_objects.epoch_ms import EpochMs


@dataclass(frozen=True)
class TemporalEntity(DomainObject, ABC):
    """
    Structural mixin for entities / aggregates with explicit temporal validity.

    IMPORTANT:
    - This class does NOT declare a DomainRole.
    - Concrete subclasses (Entity or Aggregate) must do so.
    """

    validity: TemporalValidity

    def __post_init__(self) -> None:
        self._validate_temporal()

    def _validate_temporal(self) -> None:
        if not isinstance(self.validity, TemporalValidity):
            raise InvariantViolation("TemporalEntity requires TemporalValidity")

    def close_validity(self, *, at: EpochMs) -> TemporalEntity:
        return replace(
            self,
            validity=self.validity.close(at=at),
        )
