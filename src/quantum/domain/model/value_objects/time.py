from datetime import UTC, datetime

from pydantic import Field

from quantum.domain.model.value_objects.base import ValueObject


class EpochMs(ValueObject):
    value: int = Field(..., ge=0, description="Unix epoch in milliseconds")

    @classmethod
    def now(cls) -> "EpochMs":
        return cls(value=int(datetime.now(tz=UTC).timestamp() * 1_000))

    @classmethod
    def from_datetime(cls, dt: datetime) -> "EpochMs":
        if dt.tzinfo is None:
            raise ValueError("datetime must be timezone-aware")
        return cls(value=int(dt.timestamp() * 1_000))
