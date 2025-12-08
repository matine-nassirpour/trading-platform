from __future__ import annotations

from typing import Any

from pydantic import Field, field_validator, model_validator

from quantum.infrastructure.config.models.base.base_settings import BaseConfigSettings
from quantum.infrastructure.config.models.base.mixins import PublicSettingsMixin
from quantum.infrastructure.config.validators.runtime import validate_field
from quantum.infrastructure.config.value_objects.directory_path_spec import (
    DirectoryPathSpec,
)


class LoggingSettings(BaseConfigSettings, PublicSettingsMixin):
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
        ge=0,  # >= 0
        description="Log sampling frequency for INFO-level messages "
        "(every Nth INFO log is kept if sampling enabled).",
    )
    quantum_log_ratelimit: bool = Field(
        default=False,
        description="Enable log rate limiting to prevent output flooding.",
    )
    quantum_log_rps: int = Field(
        default=100,
        ge=0,
        description="Maximum log entries per second when rate limiting is active.",
    )
    quantum_log_fsync: bool = Field(
        default=False,
        description="Force fsync on log writes (useful for crash diagnostics, slower).",
    )
    quantum_log_max_bytes: int = Field(
        default=10 * 1024 * 1024,
        ge=0,
        description="Maximum size (in bytes) per log file before rotation.",
    )
    quantum_log_warn_bytes: int = Field(
        default=0,
        ge=0,
        description="Optional warning threshold for log file size (0 = disabled).",
    )
    quantum_log_dir: DirectoryPathSpec = Field(
        description="Base directory for partitioned JSONL logs."
    )

    # --------------------------------------------------------------------------
    # Audit
    # --------------------------------------------------------------------------
    quantum_audit_dir: DirectoryPathSpec = Field(
        description="Directory for audit event JSONL files."
    )
    quantum_audit_allowlist: frozenset[str] = Field(
        default_factory=frozenset,
        description="Comma-separated list of audit events.",
    )

    # --------------------------------------------------------------------------
    # Validators
    # --------------------------------------------------------------------------
    @model_validator(mode="after")
    def validate_cross_invariants(self) -> LoggingSettings:
        # Log dir and audit dir must never be equal
        if self.quantum_log_dir.as_path() == self.quantum_audit_dir.as_path():
            raise ValueError(
                "log_dir and audit_dir must be distinct directories "
                "(safety-grade requirement: separation of logging and audit streams)."
            )

        # Ratelimit logic cross-check
        if self.quantum_log_ratelimit and self.quantum_log_rps == 0:
            raise ValueError(
                "quantum_log_rps must be > 0 when rate limiting is enabled."
            )

        return self

    @field_validator("quantum_log_level", mode="before")
    @classmethod
    def validate_log_level(cls, v: Any) -> Any:
        return validate_field(
            "platform.logging.log_level",
            v,
            field="quantum_log_level",
            model="LoggingSettings",
        )

    @field_validator("quantum_audit_allowlist", mode="before")
    @classmethod
    def parse_allowlist(cls, v):
        if v is None or v == "":
            return frozenset()
        if isinstance(v, str):
            parts = [s.strip() for s in v.split(",") if s.strip()]
            return frozenset(parts)
        return frozenset(v)

    @field_validator("quantum_log_sample_info", mode="before")
    @classmethod
    def normalize_sample_info(cls, v: Any) -> int:
        if v in ("", None):
            return 0
        return int(v)
