import re
import uuid

from typing import Any, Final, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

# ╭────────────────────────────────────────────────────────────────────────────╮
# │ Constants                                                                  │
# ╰────────────────────────────────────────────────────────────────────────────╯
SeverityText = Literal["TRACE", "DEBUG", "INFO", "WARN", "ERROR", "FATAL"]
_ALLOWED_LEVELS: Final[set[str]] = {"TRACE", "DEBUG", "INFO", "WARN", "ERROR", "FATAL"}
_HEX_RE: Final[re.Pattern[str]] = re.compile(r"^[0-9a-f]+$")


# ╭────────────────────────────────────────────────────────────────────────────╮
# │ Exception structure                                                        │
# ╰────────────────────────────────────────────────────────────────────────────╯
class ExceptionBlock(BaseModel):
    """
    Unified, structured exception block.

    This is the *single* place where exception-related fields are defined.
    All upstream components (formatters, preprocessors, factories)
    must populate this object, never individual fields.
    """

    exception: str | None = None
    exception_type: str | None = None
    exception_message: str | None = None
    exception_stacktrace: str | None = None

    model_config = ConfigDict(extra="forbid")


# ╭────────────────────────────────────────────────────────────────────────────╮
# │ Model Definition                                                           │
# ╰────────────────────────────────────────────────────────────────────────────╯
class LogPayloadV1(BaseModel):
    """
    Canonical structured log payload (version 1).

    This model defines the contract for all internal and external log
    representations produced by the Quantum stack. It is immutable,
    fully validated, and aligned with OpenTelemetry logging semantics.
    """

    # ─── Timestamps
    timestamp: str  # RFC3339 ms (UTC)
    ts_unix_ms: int | None = None
    ts_monotonic_ms: int | None = None

    # ─── Severity (OTel aligned)
    level: SeverityText
    severity_number: int | None = None

    # ─── Source
    logger: str
    message: str

    # ─── Environment / resource
    env: str
    instance: str
    service_name: str | None = None
    service_version: str | None = None
    service_namespace: str | None = None

    # ─── Correlation
    trace_id: str | None
    span_id: str | None
    sampled: bool | None
    correlation_id: str | None
    run_id: str | None

    # ─── Exceptions (structured)
    exception_block: ExceptionBlock = Field(
        default_factory=ExceptionBlock,
        description="Normalized unified exception information",
    )

    # ─── Schema metadata
    schema_name: str = Field(
        default="quantum.log",
        serialization_alias="schema",
        validation_alias="schema",
    )
    log_schema_version: str = "v1"
    validation_error: str | None = None

    # ─── Flexible attributes
    attrs: dict[str, Any] = Field(default_factory=dict)

    # --------------------------------------------------------------------------
    # Model configuration
    # --------------------------------------------------------------------------
    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        populate_by_name=True,  # allow init/dump by names and aliases
    )

    # --------------------------------------------------------------------------
    # Validators
    # --------------------------------------------------------------------------
    @field_validator("level", mode="before")
    @classmethod
    def _normalize_level(cls, v: str) -> str:
        vv = (v or "").upper()
        if vv == "WARNING":  # normalize to WARN (OTel)
            return "WARN"
        if vv == "CRITICAL":  # normalize to FATAL (OTel)
            return "FATAL"
        if vv not in _ALLOWED_LEVELS:
            raise ValueError(f"Invalid level: {v!r}")
        return vv

    @field_validator("severity_number")
    @classmethod
    def _validate_severity_number(cls, v: int | None) -> int | None:
        if v is None:
            return v
        if not (1 <= v <= 24):
            raise ValueError("severity_number must be in range [1..24]")
        return v

    @field_validator("trace_id")
    @classmethod
    def _validate_trace_id(cls, v: str | None) -> str | None:
        if v is None:
            return v
        if len(v) != 32 or not _HEX_RE.match(v):
            raise ValueError("trace_id must be 32 lowercase hex chars")
        return v

    @field_validator("span_id")
    @classmethod
    def _validate_span_id(cls, v: str | None) -> str | None:
        if v is None:
            return v
        if len(v) != 16 or not _HEX_RE.match(v):
            raise ValueError("span_id must be 16 lowercase hex chars")
        return v

    @field_validator("correlation_id", "run_id")
    @classmethod
    def _validate_uuid(cls, v: str | None) -> str | None:
        if v is None:
            return v
        try:
            uuid.UUID(v)
        except Exception as e:
            raise ValueError(f"Invalid UUID: {e}") from None
        return v

    # --------------------------------------------------------------------------
    # Serialization
    # --------------------------------------------------------------------------
    def to_clean_json(self) -> str:
        """Compact JSON serialization (UTF-8 safe, excludes None)."""
        return self.model_dump_json(exclude_none=True, by_alias=True)
