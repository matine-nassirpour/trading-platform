import re
from decimal import Decimal
from typing import ClassVar

from pydantic import BaseModel, ConfigDict, field_validator

_RFC3339_MS = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z$")


class BaseEvent(BaseModel):
    """
    Immutable and strict event.

    - `event_name` and `schema_version` are class constants (unchangeable).
    - `use_enum_values=True` serializes enums into their values (str).
    """

    event_name: ClassVar[str]
    schema_version: ClassVar[int] = 1

    timestamp: str  # RFC3339 with milliseconds and Z suffix

    run_id: str | None = None
    correlation_id: str | None = None
    trace_id: str | None = None
    span_id: str | None = None

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        use_enum_values=True,
        populate_by_name=True,
        json_encoders={Decimal: str},
    )

    @field_validator("timestamp")
    @classmethod
    def _validate_ts(cls, v: str) -> str:
        if not _RFC3339_MS.match(v):
            raise ValueError("Invalid RFC3339 timestamp")
        return v
