import re
import uuid
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

SeverityText = Literal["TRACE", "DEBUG", "INFO", "WARN", "ERROR", "FATAL"]
_HEX = re.compile(r"^[0-9a-f]+$")


class LogPayloadV1(BaseModel):
    # Timestamps
    timestamp: str  # RFC3339 ms (UTC)
    ts_unix_ms: int | None = None
    ts_monotonic_ms: int | None = None

    # Severity (align OTel)
    level: SeverityText  # kept for compatibility (upper)
    severity_number: int | None = None  # OTel 1..24

    # Source
    logger: str
    message: str

    # Environment & resource
    env: str
    instance: str
    service_name: str | None = None
    service_version: str | None = None
    service_namespace: str | None = None

    # Correlation (OTel & app-level)
    trace_id: str | None
    span_id: str | None
    sampled: bool | None
    correlation_id: str | None
    run_id: str | None

    # Exceptions (structured)
    exception: str | None = None

    # Schema
    schema_name: str = Field(  # avoid shadowing BaseModel.schema
        default="quantum.log",
        serialization_alias="schema",  # -> JSON output: "schema": "quantum.log"
        validation_alias="schema",  # -> accepts input {"schema": "..."}
    )
    log_schema_version: str = "v1"
    validation_error: str | None = None

    # Flexible attrs
    attrs: dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        populate_by_name=True,  # allow init/dump by names and aliases
    )

    @field_validator("level", mode="before")
    def _normalize_level(cls, v: str) -> str:
        vv = (v or "").upper()
        if vv in ("WARNING",):  # normalize to WARN (OTel)
            return "WARN"
        if vv not in {"TRACE", "DEBUG", "INFO", "WARN", "ERROR", "FATAL"}:
            raise ValueError(f"Invalid level: {v!r}")
        return vv

    @field_validator("severity_number")
    def _check_severity_number(cls, v):
        if v is None:
            return v
        if not (1 <= v <= 24):
            raise ValueError("severity_number must be in [1..24]")
        return v

    @field_validator("trace_id")
    def _validate_trace_id(cls, v):
        if v is None:
            return v
        if len(v) != 32 or not _HEX.match(v):
            raise ValueError("trace_id must be 32 hex chars")
        return v

    @field_validator("span_id")
    def _validate_span_id(cls, v):
        if v is None:
            return v
        if len(v) != 16 or not _HEX.match(v):
            raise ValueError("span_id must be 16 hex chars")
        return v

    @field_validator("correlation_id", "run_id")
    def _validate_uuid(cls, v):
        if v is None:
            return v
        try:
            uuid.UUID(v)
        except Exception:
            raise ValueError("must be a valid UUID")
        return v

    def to_clean_json(self) -> str:
        return self.model_dump_json(exclude_none=True, by_alias=True)
