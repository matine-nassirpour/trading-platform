import datetime
import re
import uuid

from collections.abc import Mapping
from typing import Any, Final, TypeVar

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from quantum.infrastructure.observability.logging.foundation.constants.severity_map import (
    SeverityText,
    severity_number_from_text,
)

_ALLOWED_LEVELS: Final[set[str]] = {"TRACE", "DEBUG", "INFO", "WARN", "ERROR", "FATAL"}
_HEX_RE: Final[re.Pattern[str]] = re.compile(r"^[0-9a-f]+$")

# Accepts: 2023-10-08T14:05:33.123Z
# Rejects: missing Z, missing ms, timezone offsets, lowercase z, invalid date, etc.
_RFC3339_MS_UTC_RE: Final[re.Pattern[str]] = re.compile(
    r"^(\d{4})-(\d{2})-(\d{2})T" r"(\d{2}):(\d{2}):(\d{2})\.(\d{3})Z$"
)

T = TypeVar("T", bound="LogPayload")


class ExceptionBlock(BaseModel):
    """
    Unified, structured exception block.

    All upstream components (formatting, preprocessors, factories)
    must populate this object, never individual fields.
    """

    exception_summary: str | None = None
    exception_type: str | None = None
    exception_message: str | None = None
    exception_stacktrace: str | None = None

    model_config = ConfigDict(extra="forbid")


class LogPayload(BaseModel):
    """
    Canonical structured log payload (version 1).

    This model defines the contract for all internal and external log
    representations produced by the Quantum stack. It is immutable,
    fully validated, and aligned with OpenTelemetry logging semantics.
    """

    # Timestamps
    timestamp: str  # RFC3339 ms (UTC)
    ts_unix_ms: int | None = None
    ts_monotonic_ms: int | None = None

    # Severity (OTel aligned)
    level: SeverityText
    severity_number: int | None = None

    # Source
    logger: str
    message: str

    # Environment / resource
    env: str
    instance_id: str
    service_name: str | None = None
    service_version: str | None = None
    service_namespace: str | None = None

    # Correlation
    trace_id: str | None
    span_id: str | None
    sampled: bool | None
    correlation_id: str | None
    run_id: str | None

    # Exceptions (structured)
    exception_block: ExceptionBlock = Field(
        default_factory=ExceptionBlock,
        description="Normalized unified exception information",
    )

    # Schema metadata
    schema_name: str = Field(
        default="quantum.log",
        serialization_alias="schema",
        validation_alias="schema",
    )
    log_schema_version: str = "v1"
    validation_error: str | None = None

    # Flexible attributes
    attrs: Mapping[str, Any] = Field(default_factory=dict)

    # Model configuration
    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        populate_by_name=True,  # allow init/dump by names and aliases
    )

    # --- Validators -----------------------------------------------------------
    @field_validator("timestamp")
    @classmethod
    def _validate_timestamp_rfc3339(cls, v: str) -> str:
        """
        Validate the timestamp with strict RFC3339 requirements:
            - UTC only (suffix 'Z')
            - Mandatory milliseconds
            - Zero tolerance on formatting deviations
            - Rejects timezone offsets, missing ms, lowercase z, etc.

        This ensures forensic-level consistency and safety-critical reliability.
        """
        if not isinstance(v, str):
            raise ValueError("timestamp must be a string")

        # Quick structural validation
        match = _RFC3339_MS_UTC_RE.match(v)
        if not match:
            raise ValueError(
                f"timestamp must be RFC3339 UTC with milliseconds (e.g. 2023-10-08T14:05:33.123Z). Got: {v!r}"
            )

        try:
            ts = v.rstrip("Z") + "+00:00"
            datetime.datetime.fromisoformat(ts)
        except Exception:
            raise ValueError(
                f"timestamp is not a valid RFC3339 datetime: {v!r}"
            ) from None

        return v

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

    @model_validator(mode="after")
    def _validate_severity_pair(self: T) -> T:
        """
        Validate strict consistency between:
            - level (SeverityText)
            - severity_number (int)

        Rules:
            - If severity_number is provided → must match the canonical mapping.
            - If severity_number is None → allow it (will be filled upstream).
            - level ALWAYS controls the canonical value to ensure invariance.

        This validator enforces schema integrity and guarantees that logs
        cannot carry inconsistent severity semantics, which is essential
        for forensic analysis, SIEM ingestion, and OTel alignment.
        """
        canonical_number = severity_number_from_text(self.level)

        # If severity_number is provided → strictly enforce consistency
        if self.severity_number is not None:
            if self.severity_number != canonical_number:
                raise ValueError(
                    f"Inconsistent severity: level={self.level!r} "
                    f"implies severity_number={canonical_number}, "
                    f"but got {self.severity_number}"
                )

        # Otherwise: accept severity_number=None (assembler will set it)
        return self

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

    # --- Serialization --------------------------------------------------------
    def to_clean_json(self) -> str:
        """Compact JSON serialization (UTF-8 safe, excludes None)."""
        return self.model_dump_json(exclude_none=True, by_alias=True)
