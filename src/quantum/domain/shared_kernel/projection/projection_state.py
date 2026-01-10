from abc import ABC
from dataclasses import dataclass

from quantum.domain.shared_kernel.architecture.domain_charter import DomainRole
from quantum.domain.shared_kernel.primitives.value_object import ValueObject


@dataclass(frozen=True)
class ProjectionState(ValueObject, ABC):
    """
    Base class for all derived (projected) states.

    Properties:
    - Immutable
    - Fully derived from domain events
    - Reconstructible at any time
    """

    @classmethod
    def role(cls) -> DomainRole:
        return DomainRole.READ_MODEL
