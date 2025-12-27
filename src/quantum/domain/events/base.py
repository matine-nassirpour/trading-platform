from abc import ABC
from dataclasses import dataclass, fields
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

    # --- Schema introspection -------------------------------------------------

    @classmethod
    def schema(cls) -> dict[str, str]:
        """
        Returns a stable, ordered representation of the event schema.
        """
        return {field.name: field.type.__name__ for field in fields(cls) if field.init}

    @classmethod
    def schema_id(cls) -> str:
        """
        Deterministic schema fingerprint.
        """
        items = sorted(cls.schema().items())
        return "|".join(f"{k}:{v}" for k, v in items)
