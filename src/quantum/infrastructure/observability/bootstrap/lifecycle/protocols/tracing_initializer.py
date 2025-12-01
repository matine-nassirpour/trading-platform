from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

from quantum.infrastructure.observability.bootstrap.lifecycle.configs.tracing_config import (
    TracingConfig,
)


@runtime_checkable
class TracingInitializer(Protocol):
    """
    Defines how the OpenTelemetry tracing subsystem must be initialized
    within the Quantum observability pipeline.

    Implementations control:
      • TracerProvider lifecycle
      • Exporter creation (OTLP, console, none)
      • Sampler configuration
      • Context propagation installation
      • Graceful shutdown
    """

    def initialize(self, config: TracingConfig) -> Any:
        """
        Initialize tracing and return the tracer provider instance.

        Returns:
            An opaque tracer provider object (implementation-defined).
        """
        ...

    def shutdown(self) -> None:
        """Gracefully shut down the tracing pipeline."""
        ...
