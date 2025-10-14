"""
Quantum Shared Configuration
───────────────────────────────────────────────────────────────────────────────
Centralized, validated environment configuration for all Quantum components.

This replaces ad-hoc os.getenv() calls with a structured, typed, and
validated Pydantic BaseSettings configuration.

The settings are automatically loaded from the environment and .env file,
and are cached for fast access across modules.
"""

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # ────────────────────────────────
    # Core identity
    # ────────────────────────────────
    quantum_app_name: str = Field(
        "python_core", description="Service name for tracing/logging"
    )
    quantum_app_version: str = Field(
        "0.0.0+dev", description="Application version (SemVer)"
    )
    quantum_env: str = Field("dev", description="Runtime environment")
    quantum_ns: str = Field(
        "quantum", description="Logical namespace for metrics/traces"
    )
    quantum_service_instance_id: str | None = Field(
        None, description="Stable service instance ID (e.g. desk-01)"
    )

    # ────────────────────────────────
    # Logging
    # ────────────────────────────────
    quantum_log_level: str = Field("INFO")
    quantum_log_sample_info: int = 10
    quantum_log_ratelimit: bool = False
    quantum_log_rps: int = 100
    quantum_log_fsync: bool = False
    quantum_log_max_bytes: int = 10 * 1024 * 1024
    quantum_log_warn_bytes: int = 0
    quantum_log_deep_probe: bool = False

    quantum_log_dir: Path | None = Field(
        None, description="Base directory for JSONL logs"
    )
    quantum_audit_dir: Path | None = Field(
        None, description="Base directory for audit logs"
    )
    quantum_audit_events: str | None = None
    quantum_audit_events_version: str | None = "v1"

    # ────────────────────────────────
    # Tracing
    # ────────────────────────────────
    quantum_trace_sample: float = 1.0
    quantum_trace_exporter: Literal["otlp", "console", "none"] = "console"
    quantum_trace_otlp_protocol: str = "http"
    quantum_trace_otlp_endpoint: str = "http://127.0.0.1:4318"
    quantum_trace_otlp_headers: str | None = None
    quantum_trace_otlp_timeout_ms: int = 1000
    quantum_trace_otlp_compression: Literal["gzip", "none"] = "none"
    quantum_trace_otlp_insecure: bool = True

    # ────────────────────────────────
    # Metrics
    # ────────────────────────────────
    quantum_metrics_port: int = 0
    quantum_metrics_addr: str = "0.0.0.0"

    # ────────────────────────────────
    # Streamlit (UI)
    # ────────────────────────────────
    streamlit_log_tz: Literal["utc", "local"] = "utc"
    streamlit_log_renderer: Literal["json", "code"] = "json"
    streamlit_log_expanded: bool = False
    streamlit_log_chunk_bytes: int = 256_000
    streamlit_log_tail_max_lines: int = 100
    streamlit_log_glob: str = "events-*.jsonl"

    # ────────────────────────────────
    # MT5 configuration
    # ────────────────────────────────
    quantum_mt5_ftmo_login: int | None = None
    quantum_mt5_ftmo_server: str | None = None
    quantum_mt5_ftmo_password: str | None = None

    quantum_mt5_fundednext_login: int | None = None
    quantum_mt5_fundednext_server: str | None = None
    quantum_mt5_fundednext_password: str | None = None

    mt5_ftmo_terminal_path: Path | None = None
    mt5_fundednext_terminal_path: Path | None = None

    # ────────────────────────────────
    # Execution resilience policy
    # ────────────────────────────────
    quantum_exec_timeout: float = 5.0
    quantum_exec_retries: int = 3
    quantum_exec_backoff: float = 0.5
    quantum_exec_backoff_max: float = 5.0

    # ────────────────────────────────
    # Derived validation
    # ────────────────────────────────
    @field_validator("quantum_env", mode="before")
    def normalize_env(cls, v):
        if not v:
            return "dev"
        return str(v).strip().lower()

    @field_validator("quantum_env")
    def validate_env(cls, v):
        allowed = {"dev", "staging", "prod", "test"}
        if v not in allowed:
            raise ValueError(f"Invalid QUANTUM_ENV={v!r}, must be one of {allowed}")
        return v

    @field_validator("quantum_log_level", mode="before")
    def normalize_log_level(cls, v):
        if not v:
            return "INFO"
        return str(v).strip().upper()

    @field_validator("quantum_log_level")
    def validate_log_level(cls, v):
        allowed = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        if v not in allowed:
            raise ValueError(
                f"Invalid QUANTUM_LOG_LEVEL={v!r}, must be one of {allowed}"
            )
        return v

    @field_validator("quantum_trace_sample")
    def validate_trace_sample(cls, v: float) -> float:
        if not (0.0 <= v <= 1.0):
            raise ValueError("QUANTUM_TRACE_SAMPLE must be in [0.0, 1.0]")
        return v

    @field_validator("quantum_log_sample_info", mode="before")
    def empty_str_to_zero(cls, v):
        if v in ("", None):
            return 0
        return v

    @field_validator("quantum_trace_otlp_protocol", mode="after")
    def validate_otlp_protocol(cls, v):
        allowed = {"http", "grpc"}
        if v not in allowed:
            return v
        return v

    @model_validator(mode="after")
    def validate_credentials(self):
        """Check MT5 credentials consistency if any login is provided."""
        if self.quantum_mt5_ftmo_login and not all(
            [self.quantum_mt5_ftmo_server, self.quantum_mt5_ftmo_password]
        ):
            raise ValueError("Incomplete FTMO credentials.")
        if self.quantum_mt5_fundednext_login and not all(
            [self.quantum_mt5_fundednext_server, self.quantum_mt5_fundednext_password]
        ):
            raise ValueError("Incomplete FUNDEDNEXT credentials.")
        return self

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )


# ──────────────────────────────────────────────────────────────────────────────
# Cached accessors
# ──────────────────────────────────────────────────────────────────────────────
@lru_cache
def get_settings() -> Settings:
    """Returns cached validated settings instance."""
    return Settings()
