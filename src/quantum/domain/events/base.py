from abc import ABC
from dataclasses import dataclass
from datetime import datetime
from typing import ClassVar

from quantum.domain.model.exceptions.validation_exceptions import InvariantViolation


@dataclass(frozen=True)
class BaseEvent(ABC):
    """
    Canonical immutable Domain Event.

    Guarantees:
    - Immutable
    - Versioned
    - Schema-introspectable
    """

    event_name: ClassVar[str]
    event_version: ClassVar[int] = 1
    occurred_at: datetime

    def __post_init__(self) -> None:
        if self.occurred_at.tzinfo is None:
            raise InvariantViolation("Event timestamp must be timezone-aware")
