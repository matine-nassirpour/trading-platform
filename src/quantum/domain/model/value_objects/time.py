from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

from quantum.domain.model.exceptions.validation_exceptions import InvariantViolation
from quantum.domain.model.value_objects.base import ValueObject


@dataclass(frozen=True)
class EpochMs(ValueObject):
    """
    Milliseconds since Unix epoch (UTC).

    Deterministic, integer-based time representation.
    """

    value: int

    def _validate(self) -> None:
        if not isinstance(self.value, int) or self.value < 0:
            raise InvariantViolation("EpochMs must be a non-negative integer")

    def to_datetime(self) -> datetime:
        seconds = self.value // 1000
        milliseconds = self.value % 1000

        return datetime.fromtimestamp(seconds, tz=UTC).replace(
            microsecond=milliseconds * 1000
        )

    @classmethod
    def from_datetime(cls, dt: datetime) -> EpochMs:
        if dt.tzinfo is None:
            raise InvariantViolation("Datetime must be timezone-aware")

        seconds = int(dt.timestamp())
        milliseconds = dt.microsecond // 1000

        return cls(seconds * 1000 + milliseconds)
