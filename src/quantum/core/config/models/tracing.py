"""
Quantum Core Configuration Models — Tracing Settings
────────────────────────────────────────────────────────────────────────────────
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

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class TracingSettings(BaseModel):
    """
    Structured configuration model for tracing and telemetry subsystems.
    """

    # -------------------------------------------------------------------------
    # Exporter type
    # -------------------------------------------------------------------------
    quantum_trace_exporter: Literal["otlp", "console", "none"] = Field(
        default="console",
        description="Tracing exporter type ('otlp', 'console', or 'none').",
    )

    # -------------------------------------------------------------------------
    # OTLP endpoint & connection parameters
    # -------------------------------------------------------------------------
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

    # -------------------------------------------------------------------------
    # Sampling
    # -------------------------------------------------------------------------
    quantum_trace_sample: float = Field(
        default=1.0,
        description="Trace sampling ratio in [0.0, 1.0] (fraction of traces kept).",
    )

    # -------------------------------------------------------------------------
    # Validators
    # -------------------------------------------------------------------------
    @field_validator("quantum_trace_sample")
    @classmethod
    def validate_sample(cls, v):
        if not (0.0 <= v <= 1.0):
            raise ValueError("quantum_trace_sample must be in [0, 1]")
        return v

    @field_validator("quantum_trace_otlp_protocol", mode="before")
    @classmethod
    def normalize_protocol(cls, v):
        if not v:
            return "http"
        v = str(v).strip().lower()
        if v not in ("http", "grpc"):
            # Instead of failing hard, fallback gracefully
            import logging

            logging.getLogger(__name__).warning(
                f"Unsupported OTLP protocol '{v}', defaulting to 'http'."
            )
            return "http"
        return v

    @field_validator("quantum_trace_otlp_protocol")
    @classmethod
    def validate_protocol(cls, v: str) -> str:
        v = v.strip().lower()
        if v not in ("http", "grpc"):
            raise ValueError("quantum_trace_otlp_protocol must be 'http' or 'grpc'")
        return v

    @field_validator("quantum_trace_otlp_compression")
    @classmethod
    def validate_compression(cls, v: str) -> str:
        v = v.strip().lower()
        if v not in ("gzip", "none"):
            raise ValueError("quantum_trace_otlp_compression must be 'gzip' or 'none'")
        return v

    # -------------------------------------------------------------------------
    # Model configuration
    # -------------------------------------------------------------------------
    model_config = ConfigDict(
        extra="ignore",
        frozen=True,
    )
