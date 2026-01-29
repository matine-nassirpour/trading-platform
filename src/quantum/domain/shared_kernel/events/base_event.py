import re

from abc import ABC
from dataclasses import dataclass, fields
from typing import ClassVar

from quantum.domain.shared_kernel.errors.invariants import InvariantViolation

_EVENT_NAME_PATTERN = re.compile(
    r"^[a-z]+(\.[a-z0-9_]+)+$"
)  # Example: 'trading.order.created' or 'position.sl_tp.changed'

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

    def _validate_event_identity(self) -> None:
        if not isinstance(self.event_name, str) or not self.event_name:
            raise InvariantViolation(
                f"{self.__class__.__name__}: event_name must be a non-empty string"
            )

        if not _EVENT_NAME_PATTERN.match(self.event_name):
            raise InvariantViolation(
                f"{self.__class__.__name__}: "
                f"event_name '{self.event_name}' does not match canonical format"
            )

        if not isinstance(self.event_version, int) or self.event_version < 1:
            raise InvariantViolation(
                f"{self.__class__.__name__}: event_version must be >= 1"
            )

    def _validate_fields(self) -> None:
        for f in fields(self):
            if f.name in _FORBIDDEN_EVENT_FIELDS:
                raise InvariantViolation(
                    f"{self.__class__.__name__} illegally defines forbidden field '{f.name}'"
                )

    def __post_init__(self) -> None:
        self._validate_event_identity()
        self._validate_fields()
