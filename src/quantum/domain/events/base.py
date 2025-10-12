from decimal import Decimal
from typing import ClassVar

from pydantic import BaseModel, ConfigDict, field_validator

from quantum.shared.time.format import require_rfc3339_ms


class BaseEvent(BaseModel):
    """
    Immutable and strict event.

    - `event_name` and `schema_version` are class constants (unchangeable).
    - `use_enum_values=True` serializes enums into their values (str).
    """

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        use_enum_values=True,
        populate_by_name=True,
        json_encoders={Decimal: str},
    )

    # Constants (defined in subclasses)
    event_name: ClassVar[str]
    schema_version: ClassVar[int] = 1

    # Common fields
    timestamp: str  # RFC3339 with milliseconds and Z suffix

    run_id: str | None = None
    correlation_id: str | None = None
    trace_id: str | None = None
    span_id: str | None = None

    @field_validator("timestamp")
    @classmethod
    def _validate_ts(cls, v: str) -> str:
        return require_rfc3339_ms(v)
