from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class LogPayloadV1(BaseModel):
    timestamp: str  # RFC3339 ms
    ts_unix_ms: int | None = None
    ts_monotonic_ms: int | None = None
    level: str  # DEBUG/INFO/WARNING/ERROR/CRITICAL
    logger: str
    message: str
    env: str  # deployment env (dev/stage/prod)
    instance: str  # hostname/node id
    trace_id: str | None
    span_id: str | None
    sampled: bool | None
    correlation_id: str | None
    run_id: str | None
    exception: str | None = None
    log_schema_version: str = "v1"
    validation_error: str | None = None

    attrs: dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
    )

    def to_clean_json(self) -> str:
        return self.model_dump_json(exclude_none=True, by_alias=True)
