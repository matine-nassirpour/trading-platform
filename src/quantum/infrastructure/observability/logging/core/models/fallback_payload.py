from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class FallbackPayload(BaseModel):
    """
    Contractual structured fallback schema for logging.

    Guarantees:
      - Always valid JSON
      - Always same structure (versioned schema)
      - Includes minimal mandatory fields
      - Can be safely indexed / searched / parsed
      - NEVER depends on LogRecord (pure domain)
    """

    # Core schema metadata
    schema_name: str = Field(default="quantum.log")
    log_schema_version: str = Field(default="v1_fallback")

    # Timestamps
    timestamp: str | None = None
    ts_unix_ms: int | None = None
    ts_monotonic_ms: int | None = None

    # Severity
    level: str = "ERROR"
    severity_number: int = 17  # OTel numeric code for ERROR

    # Core message
    logger: str = "fallback_logger"
    message: str = "failed to construct LogPayload"

    # Context
    env: str | None = None
    instance: str | None = None
    service_name: str | None = None
    service_version: str | None = None
    service_namespace: str | None = None

    # Correlation
    trace_id: str | None = None
    span_id: str | None = None
    sampled: bool | None = None
    correlation_id: str | None = None
    run_id: str | None = None

    # Diagnostic fields
    validation_error: str | None = None
    attrs: dict[str, Any] = Field(default_factory=dict)
    fallback_reason: str = Field(default="model_validation_failure")

    model_config = ConfigDict(frozen=True, extra="forbid")

    def to_json(self) -> str:
        return self.model_dump_json(exclude_none=True)
