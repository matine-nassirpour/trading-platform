from __future__ import annotations

from abc import ABC
from dataclasses import dataclass, replace

from quantum.domain.shared_kernel.architecture.domain_charter import DomainRole
from quantum.domain.shared_kernel.architecture.domain_object import DomainObject
from quantum.domain.shared_kernel.errors.invariants import InvariantViolation
from quantum.domain.shared_kernel.temporal.temporal_validity import TemporalValidity
from quantum.domain.shared_kernel.value_objects.epoch_ms import EpochMs


@dataclass(frozen=True)
class TemporalEntity(DomainObject, ABC):
    """
    Mixin for entities / aggregates with explicit temporal validity.
    """

    validity: TemporalValidity

    @classmethod
    def role(cls) -> DomainRole:
        # Not a concrete domain role — it is a structural mixin
        return DomainRole.ENTITY

    def __post_init__(self) -> None:
        self._validate_temporal()

    def _validate_temporal(self) -> None:
        if not isinstance(self.validity, TemporalValidity):
            raise InvariantViolation("TemporalEntity requires TemporalValidity")

    def close_validity(self, *, at: EpochMs) -> TemporalEntity:
        """
        Returns a new instance with closed temporal validity.
        """
        return replace(
            self,
            validity=self.validity.close(at=at),
        )
