from typing import Literal

from pydantic import BaseModel


class BaseEvent(BaseModel):
    event_name: str
    timestamp: str
    run_id: str | None = None
    correlation_id: str | None = None
    trace_id: str | None = None
    span_id: str | None = None
    log_schema_version: Literal["v1"] = "v1"
