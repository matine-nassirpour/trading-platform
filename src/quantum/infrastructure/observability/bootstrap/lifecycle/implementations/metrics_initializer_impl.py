from __future__ import annotations

from prometheus_client import start_http_server

from quantum.infrastructure.observability.bootstrap.lifecycle.configs.metrics_config import (
    MetricsConfig,
)
from quantum.infrastructure.observability.bootstrap.lifecycle.protocols.metrics_initializer import (
    MetricsInitializer,
)


class MetricsInitializerImpl(MetricsInitializer):
    """
    Concrete implementation of MetricsInitializer that starts the Prometheus
    HTTP exporter if configured.
    """

    def __init__(self) -> None:
        self._running = False

    def initialize(self, config: MetricsConfig) -> bool:
        if not config.enabled:
            return False

        try:
            start_http_server(port=config.port, addr=config.host)
            self._running = True
            return True
        except OSError:
            self._running = False
            return False
