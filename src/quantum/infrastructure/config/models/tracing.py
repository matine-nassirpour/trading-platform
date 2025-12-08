from __future__ import annotations

from typing import Any, Literal

from pydantic import Field, field_validator, model_validator

from quantum.infrastructure.config.models.base.base_settings import BaseConfigSettings
from quantum.infrastructure.config.models.base.mixins import PublicSettingsMixin
from quantum.infrastructure.config.validators.runtime import validate_field


class TracingSettings(BaseConfigSettings, PublicSettingsMixin):
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
    # Sensitive Fields
    # --------------------------------------------------------------------------
    @classmethod
    def sensitive_fields(cls):
        return ("quantum_trace_otlp_headers",)

    # --------------------------------------------------------------------------
    # Validators
    # --------------------------------------------------------------------------
    @model_validator(mode="after")
    def validate_endpoint_protocol(self) -> TracingSettings:
        proto = self.quantum_trace_otlp_protocol
        endpoint = self.quantum_trace_otlp_endpoint

        if proto == "http":
            if not (endpoint.startswith("http://") or endpoint.startswith("https://")):
                raise ValueError(
                    "OTLP HTTP protocol requires endpoint starting with http:// or https://"
                )

        if proto == "grpc":
            # GRPC endpoints must not include scheme
            if "://" in endpoint:
                raise ValueError(
                    "OTLP gRPC protocol requires raw host:port endpoint "
                    "(no URL scheme allowed)."
                )

        return self

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
