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
