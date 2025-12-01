from __future__ import annotations

from dataclasses import dataclass

from quantum.infrastructure.observability.foundation.config.observability_runtime_bundle import (
    ObservabilityRuntimeBundle,
)


@dataclass(frozen=True)
class TracingRuntimeBundle(ObservabilityRuntimeBundle):
    trace_exporter: str

    trace_otlp_endpoint: str
    trace_otlp_protocol: str
    trace_otlp_headers: str
    trace_otlp_timeout_ms: int
    trace_otlp_compression: str
    trace_otlp_insecure: bool

    trace_sample: float
