from abc import ABC
from dataclasses import is_dataclass
from typing import ClassVar

from quantum.domain.shared_kernel.architecture.domain_charter import DomainRole
from quantum.domain.shared_kernel.architecture.domain_object import DomainObject
from quantum.domain.shared_kernel.architecture.immutable_dataclass import (
    immutable_dataclass,
)
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


@immutable_dataclass
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
        cls = type(self)

        if not is_dataclass(cls):
            raise TypeError(f"{cls.__name__} must be a dataclass")

        for name in cls.__dataclass_fields__:
            if name in _FORBIDDEN_EVENT_FIELDS:
                raise TypeError(
                    f"{cls.__name__} illegally defines forbidden field '{name}'"
                )
