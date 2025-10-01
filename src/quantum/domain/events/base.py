import re
from typing import Literal

from pydantic import BaseModel, ConfigDict, field_validator

RFC3339_MS = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z$")


class BaseEvent(BaseModel):
    event_name: str
    timestamp: str
    run_id: str | None = None
    correlation_id: str | None = None
    trace_id: str | None = None
    span_id: str | None = None
    log_schema_version: Literal["v1"] = "v1"

    model_config = ConfigDict(extra="forbid", frozen=True)

    @field_validator("timestamp")
    @classmethod
    def _validate_ts(cls, v: str) -> str:
        if not RFC3339_MS.match(v):
            raise ValueError(
                "timestamp must be RFC3339 with millisecond precision and Z suffix"
            )
        return v
