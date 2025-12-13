from __future__ import annotations

from typing import Any

from pydantic import Field, field_validator, model_validator

from quantum.infrastructure.config.models.base.base_settings import BaseConfigSettings
from quantum.infrastructure.config.models.base.mixins import PublicSettingsMixin
from quantum.infrastructure.config.validators.runtime import validate_field


class CoreSettings(BaseConfigSettings, PublicSettingsMixin):
    """
    Structured and validated configuration for the Quantum platform runtime.

    Contains environment-agnostic parameters describing identity,
    execution, and metrics binding.
    """

    # --------------------------------------------------------------------------
    # Core identity
    # --------------------------------------------------------------------------
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

    # --------------------------------------------------------------------------
    # Metrics
    # --------------------------------------------------------------------------
    quantum_metrics_host: str = Field("0.0.0.0")  # nosec B104
    quantum_metrics_port: int = Field(0, ge=0)

    # --------------------------------------------------------------------------
    # Admin HTTP Runtime EntryPoint
    # --------------------------------------------------------------------------
    quantum_admin_http_enabled: bool = Field(False)
    quantum_admin_http_host: str = Field("127.0.0.1")
    quantum_admin_http_port: int = 8765
    quantum_admin_http_base_path: str = Field("/")
    quantum_admin_http_token: str | None = Field(
        default=None,
        repr=False,  # CRITICAL: never displayed
        description="Bearer token for admin HTTP control-plane authentication.",
    )

    # --------------------------------------------------------------------------
    # Execution policy
    # --------------------------------------------------------------------------
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

    # --------------------------------------------------------------------------
    # Validators
    # --------------------------------------------------------------------------
    @field_validator("quantum_env", mode="before")
    @classmethod
    def validate_environment(cls, v: Any) -> Any:
        return validate_field(
            "platform.runtime.environment",
            v,
            field="quantum_env",
            model="CoreSettings",
        )

    @model_validator(mode="after")
    def _validate_admin_http_security(self):
        if self.quantum_admin_http_enabled:
            if not self.quantum_admin_http_token:
                raise ValueError(
                    "quantum_admin_http_token is required when "
                    "quantum_admin_http_enabled is true"
                )
        return self
