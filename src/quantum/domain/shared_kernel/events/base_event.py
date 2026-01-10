from abc import ABC
from dataclasses import dataclass
from typing import ClassVar

from quantum.domain.shared_kernel.architecture.domain_charter import DomainRole
from quantum.domain.shared_kernel.architecture.domain_object import DomainObject
from quantum.domain.shared_kernel.errors.invariants import InvariantViolation
from quantum.domain.shared_kernel.value_objects.epoch_ms import EpochMs


@dataclass(frozen=True)
class BaseEvent(DomainObject, ABC):
    """
    Canonical immutable Domain Event.
    """

    event_name: ClassVar[str]
    event_version: ClassVar[int] = 1

    occurred_at: EpochMs

    @classmethod
    def role(cls) -> DomainRole:
        return DomainRole.EVENT

    def __post_init__(self) -> None:
        if not isinstance(self.occurred_at, EpochMs):
            raise InvariantViolation("BaseEvent.occurred_at must be an EpochMs")
