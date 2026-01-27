from abc import ABC
from dataclasses import dataclass, fields
from typing import ClassVar

from quantum.domain.shared_kernel.errors.invariants import InvariantViolation

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


@dataclass(frozen=True, slots=True)
class BaseEvent(ABC):
    """
    Canonical immutable Domain Event.

    A Domain Event represents:
    - WHAT happened
    - Not WHEN or WHERE it was recorded
    """

    event_name: ClassVar[str]
    event_version: ClassVar[int] = 1

    def __post_init__(self) -> None:
        if not hasattr(self, "event_name"):
            raise InvariantViolation("BaseEvent requires event_name")

        for f in fields(self):
            if f.name in _FORBIDDEN_EVENT_FIELDS:
                raise InvariantViolation(
                    f"{self.__class__.__name__} illegally defines forbidden field '{f.name}'"
                )
