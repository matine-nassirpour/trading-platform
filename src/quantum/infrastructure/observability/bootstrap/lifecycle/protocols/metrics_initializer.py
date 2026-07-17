from typing import Protocol, runtime_checkable

from quantum.infrastructure.observability.bootstrap.lifecycle.configs.metrics_config import (
    MetricsConfig,
)


@runtime_checkable
class MetricsInitializer(Protocol):
    """
    Protocol for initializing the Prometheus metrics HTTP exporter.

    The observability pipeline delegates all metrics-related setup to
    implementations of this interface.
    """

    def initialize(self, config: MetricsConfig) -> bool:
        """
        Start the HTTP server if enabled.

        Returns:
            True if metrics were started or explicitly disabled.
            False if startup failed.
        """
        ...
