from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from quantum.domain.model.exceptions import InvariantViolation
from quantum.domain.model.value_objects.base import ValueObject


@dataclass(frozen=True)
class EpochMs(ValueObject):
    value: int

    def _validate(self) -> None:
        if self.value < 0:
            raise InvariantViolation("EpochMs must be ≥ 0")

    @classmethod
    def from_datetime(cls, dt: datetime) -> EpochMs:
        if dt.tzinfo is None:
            raise InvariantViolation("Datetime must be timezone-aware")
        return cls(int(dt.timestamp() * 1000))
