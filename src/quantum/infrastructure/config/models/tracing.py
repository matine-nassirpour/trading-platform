"""
Quantum Core Configuration Models — Tracing Settings
────────────────────────────────────────────────────
Immutable schema defining tracing and telemetry configuration parameters
for distributed observability within the Quantum platform.

Responsibilities
----------------
- Define validated and strongly typed tracing configuration options.
- Support OpenTelemetry exporters, endpoints, and sampling configuration.
- Provide deterministic, side-effect-free tracing settings for runtime use.
- Ensure forward compatibility with additional tracing backends or formats.

Design Principles
-----------------
- **Single Responsibility** : declares tracing configuration schema only.
- **Clean Architecture** : pure model, independent of runtime logic.
- **Immutability** : frozen model ensuring deterministic behavior.
- **Validation by Contract** : explicit field normalization and checks.
- **Extensibility** : open to new protocols, exporters, or compression modes.
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from quantum.infrastructure.config.validators import validate_field


class TracingSettings(BaseModel):
    """
    Structured configuration model for tracing and telemetry subsystems.
    """

    # --------------------------------------------------------------------------
    # Exporter type
    # --------------------------------------------------------------------------
    quantum_trace_exporter: Literal["otlp", "console", "none"] = Field(
        default="console",
        description="Tracing exporter type ('otlp', 'console', or 'none').",
    )

    # --------------------------------------------------------------------------
    # OTLP endpoint & connection parameters
    # --------------------------------------------------------------------------
    quantum_trace_otlp_endpoint: str = Field(
        default="http://127.0.0.1:4318",
        description="OTLP collector endpoint URL.",
    )
    quantum_trace_otlp_protocol: Literal["http", "grpc"] = Field(
        default="http",
        description="Protocol used for OTLP transport ('http' or 'grpc').",
    )
    quantum_trace_otlp_headers: str | None = Field(
        default=None,
        description="Optional comma-separated custom headers for OTLP exporter.",
    )
    quantum_trace_otlp_timeout_ms: int = Field(
        default=1000,
        description="Timeout for OTLP transmission in milliseconds.",
    )
    quantum_trace_otlp_compression: Literal["gzip", "none"] = Field(
        default="none",
        description="Compression type used for OTLP payloads.",
    )
    quantum_trace_otlp_insecure: bool = Field(
        default=True,
        description="Allow insecure (non-TLS) connections to the OTLP endpoint.",
    )

    # --------------------------------------------------------------------------
    # Sampling
    # --------------------------------------------------------------------------
    quantum_trace_sample: float = Field(
        default=1.0,
        description="Trace sampling ratio in [0.0, 1.0] (fraction of traces kept).",
    )

    # --------------------------------------------------------------------------
    # Validators
    # --------------------------------------------------------------------------
    @field_validator("quantum_trace_otlp_protocol", mode="before")
    @classmethod
    def validate_protocol(cls, v: Any) -> Any:
        # Rule: platform.tracing.otlp_protocol
        return validate_field(
            "platform.tracing.otlp_protocol",
            v,
            field="quantum_trace_otlp_protocol",
            model="TracingSettings",
        )

    @field_validator("quantum_trace_otlp_compression", mode="before")
    @classmethod
    def validate_compression(cls, v: Any) -> Any:
        # Rule: platform.tracing.compression
        return validate_field(
            "platform.tracing.compression",
            v,
            field="quantum_trace_otlp_compression",
            model="TracingSettings",
        )

    @field_validator("quantum_trace_sample")
    @classmethod
    def validate_sample(cls, v: float) -> float:
        if not (0.0 <= v <= 1.0):
            raise ValueError("quantum_trace_sample must be in [0, 1]")
        return v

    # --------------------------------------------------------------------------
    # Model configuration
    # --------------------------------------------------------------------------
    model_config = ConfigDict(
        extra="ignore",
        frozen=True,
    )
