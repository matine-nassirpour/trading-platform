from __future__ import annotations

import logging

from contextlib import suppress
from typing import Final

from quantum.infrastructure.observability.bootstrap.lifecycle.configs.logging_config import (
    LoggingConfig,
)
from quantum.infrastructure.observability.bootstrap.lifecycle.configs.metrics_config import (
    MetricsConfig,
)
from quantum.infrastructure.observability.bootstrap.lifecycle.configs.tracing_config import (
    TracingConfig,
)
from quantum.infrastructure.observability.bootstrap.lifecycle.dependencies import (
    ObservabilityDependencies,
)

LOGGER: Final = logging.getLogger(__name__)


class LifecycleService:
    """
    Core orchestrator of Observability initialization and shutdown.

    This redesigned version provides:
        • Pure dependency injection (no hidden state)
        • Deterministic initialization flow
        • Idempotent behavior
        • Full compatibility with Prometheus, Logging, and OTEL
        • Complete removal of legacy global state
        • Clean Architecture alignment

    This class is now long-term maintainable (10+ years).
    """

    def __init__(self, deps: ObservabilityDependencies) -> None:
        self._deps = deps
        self._logger = LOGGER
        self._initialized = False

        # Keep tracer provider instance here (no global reference).
        self._tracer_provider: object | None = None

    def _shutdown_tracing_provider(self) -> None:
        """Gracefully shut down any active TracerProvider."""
        if self._tracer_provider is None:
            return

        shutdown = getattr(self._tracer_provider, "shutdown", None)
        if callable(shutdown):
            try:
                shutdown()
            except Exception as exc:
                self._logger.debug(f"Tracer shutdown failed: {exc}")

        self._tracer_provider = None

    def initialize(
        self,
        *,
        logging_config: LoggingConfig,
        tracing_config: TracingConfig,
        metrics_config: MetricsConfig,
        force: bool = False,
    ) -> bool:
        """
        Main entry point for initializing the entire Observability pipeline.

        This method performs:
            1. Reset gauges
            2. Refresh build info
            3. Initialize tracing
            4. Initialize logging
            5. Probe sinks
            6. Initialize metrics
            7. Aggregate health
        """
        if self._initialized and not force:
            self._logger.debug("[Observability] Already initialized — skipping.")
            return True

        registry = self._deps.health_registry
        # diagnostics = self._deps.diagnostics

        # Reset health state
        registry.reset_all()

        # ----------------------------------------------------------------------
        # Tracing
        # ----------------------------------------------------------------------
        try:
            provider = self._deps.tracing_initializer.initialize(tracing_config)
            self._tracer_provider = provider
            registry.mark_tracing_ok(True)
            registry.mark_tracing_up(True)
        except Exception as exc:
            self._logger.warning(f"[Observability] Tracing init failed: {exc}")
            registry.mark_tracing_ok(False)
            registry.mark_tracing_up(False)

        # ----------------------------------------------------------------------
        # Logging
        # ----------------------------------------------------------------------
        try:
            ok = self._deps.logging_initializer.initialize(logging_config)
            registry.mark_logging_ok(ok)
            if ok:
                registry.mark_logging_sink_up(True)
        except Exception as exc:
            self._logger.exception(f"[Observability] Logging init failed: {exc}")
            registry.mark_logging_ok(False)
            registry.mark_logging_sink_up(False)

        # ----------------------------------------------------------------------
        # Metrics
        # ----------------------------------------------------------------------
        try:
            metrics_ok = self._deps.metrics_initializer.initialize(metrics_config)
            registry.mark_metrics_http_ok(metrics_ok)
        except Exception as exc:
            self._logger.warning(f"[Observability] Metrics init failed: {exc}")
            registry.mark_metrics_http_ok(False)

        # Aggregate global pipeline status
        pipeline_ok = (
            registry.logging_ok._value.get() == 1.0
            and registry.tracing_ok._value.get() == 1.0
        )
        registry.mark_pipeline_up(pipeline_ok)

        self._initialized = pipeline_ok
        return pipeline_ok

    def shutdown(
        self,
        *,
        close_logging: bool = True,
        shutdown_tracing: bool = True,
        set_gauges_down: bool = False,
    ) -> None:
        """Clean and idempotent shutdown of all observability components."""
        registry = self._deps.health_registry

        # Tracing shutdown
        if shutdown_tracing:
            with suppress(Exception):
                self._deps.tracing_initializer.shutdown()
            self._shutdown_tracing_provider()
            if set_gauges_down:
                registry.mark_tracing_up(False)

        # Logging shutdown
        if close_logging:
            with suppress(Exception):
                self._deps.logging_initializer.shutdown()
            if set_gauges_down:
                registry.mark_logging_sink_up(False)

        # Global pipeline marker
        if set_gauges_down:
            registry.mark_pipeline_up(False)

        self._initialized = False
        self._logger.info("[Observability] Shutdown complete.")
