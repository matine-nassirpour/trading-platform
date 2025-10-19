from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class TracingSettings(BaseModel):
    quantum_trace_exporter: Literal["otlp", "console", "none"] = "console"
    quantum_trace_otlp_endpoint: str = Field("http://127.0.0.1:4318")
    quantum_trace_sample: float = 1.0
    quantum_trace_otlp_protocol: Literal["http", "grpc"] = Field("http")
    quantum_trace_otlp_headers: str | None = Field(None)
    quantum_trace_otlp_timeout_ms: int = Field(1000)
    quantum_trace_otlp_compression: Literal["gzip", "none"] = Field("none")
    quantum_trace_otlp_insecure: bool = Field(True)

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

    model_config = ConfigDict(
        extra="ignore",
        frozen=True,
    )
