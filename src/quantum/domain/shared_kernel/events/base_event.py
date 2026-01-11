from abc import ABC
from dataclasses import dataclass
from typing import ClassVar

from quantum.domain.shared_kernel.architecture.domain_charter import DomainRole
from quantum.domain.shared_kernel.architecture.domain_object import DomainObject


@dataclass(frozen=True)
class BaseEvent(DomainObject, ABC):
    """
    Canonical immutable Domain Event.

    A Domain Event represents:
    - WHAT happened
    - Not WHEN or WHERE it was recorded

    It is pure business fact.
    """

    event_name: ClassVar[str]
    event_version: ClassVar[int] = 1

    @classmethod
    def role(cls) -> DomainRole:
        return DomainRole.EVENT
