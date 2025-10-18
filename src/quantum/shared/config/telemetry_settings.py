"""
Quantum Telemetry Settings
──────────────────────────────────────────────────────────────────────────────
Configuration model for trace exporter transport (OTLP, Datadog, etc.).
Separated from observability_settings to isolate low-level transport details.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class TelemetrySettings(BaseModel):
    """Configuration for trace exporter transport layer."""

    quantum_trace_otlp_protocol: Literal["http", "grpc"] = Field(
        "http", description="OTLP transport protocol ('http' or 'grpc')."
    )
    quantum_trace_otlp_headers: str | None = Field(
        None, description="Custom OTLP headers (e.g. 'Authorization=Bearer x')."
    )
    quantum_trace_otlp_timeout_ms: int = Field(
        1000, description="OTLP export timeout in milliseconds."
    )
    quantum_trace_otlp_compression: Literal["gzip", "none"] = Field(
        "none", description="Compression type for OTLP payloads."
    )
    quantum_trace_otlp_insecure: bool = Field(
        True, description="Allow insecure (non-TLS) OTLP connections."
    )

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

    model_config = ConfigDict(
        extra="ignore",
        frozen=True,
    )
