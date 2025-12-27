from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

from quantum.domain.model.exceptions.validation_exceptions import InvariantViolation
from quantum.domain.model.value_objects.base import ValueObject


@dataclass(frozen=True)
class EpochMs(ValueObject):
    value: int

    def _validate(self) -> None:
        if not isinstance(self.value, int) or self.value < 0:
            raise InvariantViolation("EpochMs must be a non-negative integer")

    def to_datetime(self) -> datetime:
        return datetime.fromtimestamp(self.value / 1000, tz=UTC)

    @classmethod
    def from_datetime(cls, dt: datetime) -> EpochMs:
        if dt.tzinfo is None:
            raise InvariantViolation("Datetime must be timezone-aware")
        return cls(int(dt.timestamp() * 1000))
