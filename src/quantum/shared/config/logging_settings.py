from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, field_validator


class LoggingSettings(BaseModel):

    # ─── Logging
    quantum_log_level: str = Field("INFO")
    quantum_log_sample_info: int = Field(
        10,
        description="Log sampling frequency for INFO-level messages "
        "(every Nth INFO log is kept if sampling enabled).",
    )
    quantum_log_ratelimit: bool = Field(
        False, description="Enable log rate limiting to prevent output flooding."
    )
    quantum_log_rps: int = Field(
        100, description="Maximum log entries per second when rate limiting is active."
    )
    quantum_log_fsync: bool = Field(
        False,
        description="Force fsync on log writes (useful for crash diagnostics, slower).",
    )
    quantum_log_max_bytes: int = Field(
        10 * 1024 * 1024,
        description="Maximum size (in bytes) per log file before rotation.",
    )
    quantum_log_warn_bytes: int = Field(
        0, description="Optional warning threshold for log file size (0 = disabled)."
    )
    quantum_log_deep_probe: bool = Field(
        False, description="Enable deep internal logging for diagnostic inspection."
    )
    quantum_log_dir: str | None = Field(
        None, description="Base directory for partitioned JSONL logs."
    )

    # ─── Audit
    quantum_audit_dir: str | None = Field(
        None, description="Directory for audit event JSONL files."
    )
    quantum_audit_events: str | None = Field(
        None,
        description="Comma-separated list of event types to audit (e.g. 'order_ack_event, order_fill_event').",
    )
    quantum_audit_events_version: str = Field(
        "v1", description="Version of audit event schema."
    )

    # ─── Streamlit integration (optional visualization defaults)
    streamlit_log_tz: str = Field(
        "utc", description="Timezone for log display (utc or local)."
    )
    streamlit_log_renderer: str = Field(
        "json", description="Preferred log rendering mode ('json' or 'code')."
    )
    streamlit_log_expanded: bool = Field(
        False, description="Whether Streamlit log view is expanded by default."
    )
    streamlit_log_chunk_bytes: int = Field(
        256_000, description="Maximum chunk size (bytes) when reading log tails."
    )
    streamlit_log_tail_max_lines: int = Field(
        100,
        description="Maximum number of log lines displayed in the Streamlit tail view.",
    )
    streamlit_log_glob: str = Field(
        "events-*.jsonl", description="Glob pattern for log discovery in Streamlit UI."
    )

    # ─── Validators
    @field_validator("quantum_log_level", mode="before")
    @classmethod
    def normalize_log_level(cls, v):
        if not v:
            return "INFO"
        return str(v).strip().upper()

    @field_validator("quantum_log_level")
    @classmethod
    def validate_log_level(cls, v):
        allowed = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        if v not in allowed:
            raise ValueError(
                f"Invalid quantum_log_level={v!r}, must be one of {allowed}"
            )
        return v

    @field_validator("quantum_log_sample_info", mode="before")
    @classmethod
    def empty_str_to_zero(cls, v):
        if v in ("", None):
            return 0
        return v

    @field_validator("streamlit_log_tz")
    @classmethod
    def validate_tz(cls, v: str) -> str:
        v = v.strip().lower()
        if v not in ("utc", "local"):
            raise ValueError("streamlit_log_tz must be 'utc' or 'local'")
        return v

    @field_validator("streamlit_log_renderer")
    @classmethod
    def validate_renderer(cls, v: str) -> str:
        v = v.strip().lower()
        if v not in ("json", "code"):
            raise ValueError("streamlit_log_renderer must be 'json' or 'code'")
        return v

    model_config = ConfigDict(
        extra="ignore",
        frozen=True,
    )
