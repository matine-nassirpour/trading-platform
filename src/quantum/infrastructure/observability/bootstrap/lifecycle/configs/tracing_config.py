from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TracingConfig:
    """
    Immutable value object defining all necessary settings for initializing
    the OpenTelemetry tracing subsystem.

    This object is the *only* configuration input accepted by TracingInitializer
    in a Clean Architecture context.
    """

    exporter_type: str  # "otlp", "console", "none", ...
    exporter_endpoint: str | None

    sample_ratio: float  # 0.0 → disabled, 1.0 → full sampling

    shutdown_timeout_sec: float  # graceful shutdown duration

    service_name: str
    service_namespace: str
    service_version: str
    environment: str
    instance_id: str
