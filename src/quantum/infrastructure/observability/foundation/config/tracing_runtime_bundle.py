from __future__ import annotations

from dataclasses import dataclass

from quantum.infrastructure.observability.foundation.config.identity_runtime_bundle import (
    IdentityRuntimeBundle,
)


@dataclass(frozen=True, slots=True)
class TracingRuntimeBundle:
    """
    Pure runtime Value Object for tracing/telemetry initialization.
    All fields are normalized and validated by the factory.
    """

    identity: IdentityRuntimeBundle

    trace_exporter: str
    trace_otlp_endpoint: str
    trace_otlp_protocol: str
    trace_otlp_headers: str | None
    trace_otlp_timeout_ms: int
    trace_otlp_compression: str
    trace_otlp_insecure: bool

    trace_sample: float

    def __post_init__(self):
        if self.trace_exporter not in {"otlp", "console", "none"}:
            raise ValueError("Invalid trace_exporter type.")

        if self.trace_otlp_protocol not in {"http", "grpc"}:
            raise ValueError("trace_otlp_protocol must be 'http' or 'grpc'.")

        if self.trace_otlp_compression not in {"gzip", "none"}:
            raise ValueError("trace_otlp_compression must be 'gzip' or 'none'.")

        if not (0.0 <= self.trace_sample <= 1.0):
            raise ValueError("trace_sample must be in [0.0, 1.0].")
