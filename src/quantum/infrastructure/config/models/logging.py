"""
Quantum Core Configuration Models — Logging Settings
────────────────────────────────────────────────────
Immutable schema defining all configuration parameters related to logging
and audit subsystems within the Quantum platform.

Responsibilities
----------------
- Define validated, strongly typed logging configuration parameters.
- Enforce consistency and safety for logging, rate limiting, and rotation.
- Provide optional audit event schema and Streamlit visualization settings.
- Remain independent of any logging framework implementation.

Design Principles
-----------------
- **Single Responsibility** : declares logging configuration schema only.
- **Clean Architecture** : pure model, no side effects or dependencies.
- **Immutability** : frozen model ensuring deterministic runtime behavior.
- **Validation by Contract** : explicit field constraints and normalization.
- **Extensibility** : easily versioned and expanded without breaking changes.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from quantum.infrastructure.config.validators import validate_field


class LoggingSettings(BaseModel):
    """
    Structured configuration model for Quantum logging and audit subsystems.
    """

    # --------------------------------------------------------------------------
    # Logging
    # --------------------------------------------------------------------------
    quantum_log_level: str = Field(
        default="INFO",
        description="Global logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL).",
    )
    quantum_log_sample_info: int = Field(
        default=10,
        description="Log sampling frequency for INFO-level messages "
        "(every Nth INFO log is kept if sampling enabled).",
    )
    quantum_log_ratelimit: bool = Field(
        default=False,
        description="Enable log rate limiting to prevent output flooding.",
    )
    quantum_log_rps: int = Field(
        100, description="Maximum log entries per second when rate limiting is active."
    )
    quantum_log_fsync: bool = Field(
        default=False,
        description="Force fsync on log writes (useful for crash diagnostics, slower).",
    )
    quantum_log_max_bytes: int = Field(
        default=10 * 1024 * 1024,
        description="Maximum size (in bytes) per log file before rotation.",
        ge=0,
    )
    quantum_log_warn_bytes: int = Field(
        default=0,
        description="Optional warning threshold for log file size (0 = disabled).",
        ge=0,
    )
    quantum_log_dir: str | None = Field(
        default=None, description="Base directory for partitioned JSONL logs."
    )

    # --------------------------------------------------------------------------
    # Audit
    # --------------------------------------------------------------------------
    quantum_audit_dir: str | None = Field(
        default=None, description="Directory for audit event JSONL files."
    )
    quantum_audit_events: str | None = Field(
        default=None,
        description="Comma-separated list of event types to audit.",
    )
    quantum_audit_events_version: str = Field(
        default="v1", description="Version of audit event schema."
    )

    # --------------------------------------------------------------------------
    # Streamlit integration (optional visualization defaults)
    # --------------------------------------------------------------------------
    streamlit_log_tz: str = Field(
        default="utc", description="Timezone for log display (utc or local)."
    )
    streamlit_log_renderer: str = Field(
        default="json", description="Preferred log rendering mode ('json' or 'code')."
    )
    streamlit_log_expanded: bool = Field(
        default=False, description="Whether Streamlit log view is expanded by default."
    )
    streamlit_log_chunk_bytes: int = Field(
        default=256_000,
        description="Maximum chunk size (bytes) when reading log tails.",
    )
    streamlit_log_tail_max_lines: int = Field(
        default=100,
        description="Maximum number of log lines displayed in the Streamlit tail view.",
    )
    streamlit_log_glob: str = Field(
        default="events-*.jsonl",
        description="Glob pattern for log discovery in Streamlit UI.",
    )

    # --------------------------------------------------------------------------
    # Validators
    # --------------------------------------------------------------------------
    @field_validator("quantum_log_level", mode="before")
    @classmethod
    def validate_log_level(cls, v: Any) -> Any:
        return validate_field(
            "platform.logging.log_level",
            v,
            field="quantum_log_level",
            model="LoggingSettings",
        )

    @field_validator("streamlit_log_tz", mode="before")
    @classmethod
    def validate_tz(cls, v: Any) -> Any:
        return validate_field(
            "platform.logging.timezone",
            v,
            field="streamlit_log_tz",
            model="LoggingSettings",
        )

    @field_validator("streamlit_log_renderer", mode="before")
    @classmethod
    def validate_renderer(cls, v: str) -> str:
        if not v:
            return "json"
        v = str(v).strip().lower()
        if v not in ("json", "code"):
            raise ValueError("streamlit_log_renderer must be 'json' or 'code'")
        return v

    @field_validator("quantum_log_sample_info", mode="before")
    @classmethod
    def normalize_sample_info(cls, v: Any) -> int:
        if v in ("", None):
            return 0
        return int(v)

    # --------------------------------------------------------------------------
    # Model configuration
    # --------------------------------------------------------------------------
    model_config = ConfigDict(
        extra="ignore",
        frozen=True,
    )
