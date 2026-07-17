from prometheus_client import start_http_server

from quantum.infrastructure.observability.bootstrap.lifecycle.configs.metrics_config import (
    MetricsConfig,
)
from quantum.infrastructure.observability.foundation.system_diagnostics.c0_diagnostic_logger import (
    get_diagnostic_logger,
)
from quantum.infrastructure.observability.metrics.metrics_exporter import (
    metrics_exporter,
)


class MetricsInitializerImpl:
    """
    Concrete implementation of MetricsInitializer that starts the Prometheus
    HTTP exporter if configured.
    """

    def __init__(self) -> None:
        self._running = False

    def initialize(self, config: MetricsConfig) -> bool:
        diag = get_diagnostic_logger()

        try:
            metrics_exporter.bind_default_logging_metrics()
        except Exception as exc:
            # Log via C0 diagnostics
            diag.error(
                f"[metrics-init] failed to bind default metrics: {exc.__class__.__name__}"
            )

        if config.port <= 0:
            return True

        try:
            start_http_server(port=config.port, addr=config.host)
            self._running = True
            return True
        except OSError:
            self._running = False
            return False
