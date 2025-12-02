from __future__ import annotations

from dataclasses import dataclass

from quantum.infrastructure.observability.foundation.config.identity_runtime_bundle import (
    IdentityRuntimeBundle,
)


@dataclass(frozen=True)
class TracingConfig:
    """
    Immutable value object defining all necessary settings for initializing
    the OpenTelemetry tracing subsystem.

    This object is the *only* configuration input accepted by TracingInitializer
    in a Clean Architecture context.
    """

    identity: IdentityRuntimeBundle
    trace_exporter: str

    trace_otlp_endpoint: str
    trace_otlp_protocol: str
    trace_otlp_headers: str
    trace_otlp_timeout_ms: int
    trace_otlp_compression: str
    trace_otlp_insecure: bool

    trace_sample: float
