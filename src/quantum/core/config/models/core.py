"""
Quantum Core Configuration Models — Core Settings
────────────────────────────────────────────────────────────────────────────────
Immutable, validated schema defining the core runtime configuration used
throughout the Quantum platform.

Responsibilities
----------------
- Define environment-independent configuration structure.
- Enforce strict validation and typing for all runtime parameters.
- Provide immutable and deterministic configuration state.
- Offer a stable foundation for higher-level configuration orchestration.

Design Principles
-----------------
- **Single Responsibility** : declares schema and validation only.
- **Clean Architecture** : independent of runtime and provider layers.
- **Immutability** : frozen model ensuring deterministic behavior.
- **Strong Typing** : explicit field constraints and semantic validation.
- **Forward Compatibility** : ignores unknown fields for long-term evolution.
"""

from __future__ import annotations

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from quantum.core.config.validators import validate_field


class CoreSettings(BaseSettings):
    """
    Structured and validated configuration for the Quantum core runtime.

    Contains environment-agnostic parameters describing identity,
    execution, and metrics binding.
    """

    # -------------------------------------------------------------------------
    # Core identity
    # -------------------------------------------------------------------------
    quantum_app_name: str = Field("python_core")
    quantum_app_version: str = Field("0.0.0+dev")
    quantum_env: str = Field(
        default="dev",
        description="Runtime environment (e.g., dev, test, staging, prod).",
    )
    quantum_ns: str = Field(
        default="quantum",
        description="Namespace to group metrics/logs/resources.",
    )
    quantum_instance_id: str | None = Field(
        default=None,
        description="Optional unique instance identifier for this runtime.",
    )

    # -------------------------------------------------------------------------
    # Metrics
    # -------------------------------------------------------------------------
    quantum_metrics_addr: str = Field("0.0.0.0")
    quantum_metrics_port: int = Field(0, ge=0)

    # -------------------------------------------------------------------------
    # Execution policy
    # -------------------------------------------------------------------------
    quantum_exec_timeout: float = Field(
        default=5.0,
        description="Default upper bound (seconds) for bounded operations.",
    )
    quantum_exec_retries: int = Field(
        default=3,
        description="Number of retry attempts on transient failures.",
    )
    quantum_exec_backoff: float = Field(
        default=0.5,
        description="Initial backoff (seconds) between retries.",
    )
    quantum_exec_backoff_max: float = Field(
        default=5.0,
        description="Maximum backoff (seconds) between retries.",
    )

    # -------------------------------------------------------------------------
    # Validators
    # -------------------------------------------------------------------------
    @field_validator("quantum_env", mode="before")
    @classmethod
    def validate_environment(cls, v):
        return validate_field(
            "core.runtime.environment",
            v,
            field="quantum_env",
            model="CoreSettings",
        )

    # -------------------------------------------------------------------------
    # Settings metadata
    # -------------------------------------------------------------------------
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )
