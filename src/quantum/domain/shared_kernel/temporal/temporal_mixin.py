from __future__ import annotations

from abc import ABC
from dataclasses import dataclass, replace

from quantum.domain.shared_kernel.errors.invariants import InvariantViolation
from quantum.domain.shared_kernel.temporal.temporal_validity import TemporalValidity
from quantum.domain.shared_kernel.value_objects.epoch_ms import EpochMs


@dataclass(frozen=True)
class TemporalMixin(ABC):
    """
    Structural mixin for temporally valid domain objects.

    This class:
    - Does NOT declare a DomainRole
    - Does NOT participate in the DomainObject hierarchy
    - Is purely a structural capability

    This prevents any possibility of violating the Domain Charter.
    """

    validity: TemporalValidity

    def __post_init__(self) -> None:
        self._validate_temporal()

    def _validate_temporal(self) -> None:
        if not isinstance(self.validity, TemporalValidity):
            raise InvariantViolation("TemporalMixin requires TemporalValidity")

    def close_validity(self, *, at: EpochMs) -> TemporalMixin:
        return replace(
            self,
            validity=self.validity.close(at=at),
        )
