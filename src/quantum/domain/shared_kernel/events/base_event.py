from abc import ABC
from dataclasses import dataclass, fields
from typing import ClassVar

from quantum.domain.shared_kernel.architecture.domain_charter import DomainRole
from quantum.domain.shared_kernel.architecture.domain_object import DomainObject
from quantum.domain.shared_kernel.primitives.immutable_domain_object import (
    ImmutableDomainObject,
)

_FORBIDDEN_EVENT_FIELDS = {
    "id",
    "event_id",
    "timestamp",
    "occurred_at",
    "sequence",
    "version",
    "causation_id",
    "correlation_id",
    "stream_id",
}


@dataclass(frozen=True)
class BaseEvent(DomainObject, ImmutableDomainObject, ABC):
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

    # --- Architectural guard --------------------------------------------------

    def __post_init__(self) -> None:
        for field in fields(self):
            if field.name in _FORBIDDEN_EVENT_FIELDS:
                raise TypeError(
                    f"{self.__class__.__name__} illegally defines {field.name}"
                )
