from __future__ import annotations

import logging
import os
from contextlib import suppress
from pathlib import Path
from typing import TYPE_CHECKING

from prometheus_client import start_http_server

from quantum.infrastructure.observability.bootstrap.diagnostics import measure_latency
from quantum.infrastructure.observability.bootstrap.state import get_tracer_provider
from quantum.infrastructure.observability.logging.service import (
    close_and_remove_all_handlers,
    init_logging,
)
from quantum.infrastructure.observability.metrics.collectors.health_collector import (
    refresh_build_info_from_env,
)
from quantum.infrastructure.observability.tracing.propagation import (
    detach_process_baggage_if_any,
    install_process_baggage,
    setup_propagation,
)
from quantum.infrastructure.observability.tracing.provider import init_tracing

if TYPE_CHECKING:
    from quantum.infrastructure.observability.bootstrap.health_registry import (
        HealthRegistry,
    )
    from quantum.platform.config.models.core import CoreSettings
    from quantum.platform.config.models.logging import LoggingSettings
    from quantum.platform.config.models.tracing import TracingSettings


class LifecycleService:
    """
    Centralized orchestrator for the observability lifecycle.

    Manages initialization, probing, and teardown of all subsystems.

    Thread-safety:
        Each method is idempotent and designed to handle repeated calls
        safely without double initialization or inconsistent state.
    """

    def __init__(self, registry: HealthRegistry) -> None:
        self._registry = registry
        self._logger = logging.getLogger(__name__)
        self._tracer_provider_ref: object | None = None

    # --------------------------------------------------------------------------
    # Internal Utilities
    # --------------------------------------------------------------------------
    @staticmethod
    def _iter_persistent_handlers() -> list[logging.Handler]:
        """Return all logging handlers that have a 'base_dir' attribute."""
        handlers: list[logging.Handler] = []
        root = logging.getLogger()
        handlers.extend([h for h in root.handlers if getattr(h, "base_dir", None)])
        audit_logger = logging.getLogger("quantum.trading")
        handlers.extend(
            [h for h in audit_logger.handlers if getattr(h, "base_dir", None)]
        )
        return handlers

    @staticmethod
    def _probe_path_writable(
        base_dir: str | os.PathLike[str], *, deep_probe: bool = False
    ) -> bool:
        """Check directory writability; optionally perform deep write probe."""
        try:
            os.makedirs(base_dir, exist_ok=True)
            if not os.access(base_dir, os.W_OK):
                return False
            if deep_probe:
                base = Path(base_dir)
                probe = base / "__probe__/yyyy/mm/dd/hh"
                probe.mkdir(parents=True, exist_ok=True)
                f = probe / "probe.jsonl"
                with open(f, "a", encoding="utf-8") as fp:
                    fp.write("{}\n")
                f.unlink(missing_ok=True)
                with suppress(OSError):
                    probe.rmdir()
            return True
        except OSError:
            return False

    def _probe_logging_sinks(self, deep_probe: bool = False) -> bool:
        """Return True if at least one persistent sink is writable."""
        persistent_handlers = self._iter_persistent_handlers()
        if not persistent_handlers:
            return False
        return any(
            self._probe_path_writable(getattr(h, "base_dir", ""), deep_probe=deep_probe)
            for h in persistent_handlers
            if getattr(h, "base_dir", None)
        )

    def _shutdown_tracing_if_any(self) -> None:
        """Best-effort shutdown of the current tracer provider."""
        tp = get_tracer_provider() or self._tracer_provider_ref
        if tp is None:
            return
        shutdown = getattr(tp, "shutdown", None)
        if callable(shutdown):
            try:
                shutdown()
            except Exception as exc:
                self._logger.debug(f"Tracer shutdown failed: {exc}")
        self._tracer_provider_ref = None

    # --------------------------------------------------------------------------
    # Initialization
    # --------------------------------------------------------------------------
    @measure_latency("tracing")
    def init_tracing(
        self,
        core_settings: CoreSettings,
        tracing_settings: TracingSettings,
        force: bool = False,
    ) -> bool:
        """Initialize OpenTelemetry tracing subsystem with fallback support."""
        try:
            self._shutdown_tracing_if_any()
            tracer_provider = init_tracing(core_settings, tracing_settings, force)
            setup_propagation()
            install_process_baggage()
            self._registry.mark_tracing_up(True)
            self._tracer_provider_ref = tracer_provider
            return True

        except Exception as exc:
            self._logger.warning(f"Tracing initialization failed: {exc}")
            self._registry.mark_tracing_up(False)

            # Fallback retry
            try:
                tracing_fallback = tracing_settings.model_copy(
                    update={
                        "quantum_trace_exporter": "none",
                        "quantum_trace_sample": 0.0,
                    }
                )
                tracer_provider = init_tracing(core_settings, tracing_fallback, True)
                setup_propagation()
                install_process_baggage()
                self._registry.mark_tracing_up(True)
                self._tracer_provider_ref = tracer_provider
                self._logger.warning(
                    "Tracing fallback activated: exporter=none, sample_ratio=0.0"
                )
                return True
            except Exception as fallback_exc:
                self._logger.exception(f"Tracing fallback failed: {fallback_exc}")
                self._registry.mark_tracing_up(False)
                return False

    @measure_latency("logging")
    def init_logging_safe(
        self,
        core_settings: CoreSettings,
        logging_settings: LoggingSettings,
    ) -> bool:
        """Initialize logging with exception safety."""
        try:
            init_logging(core_settings, logging_settings)
            self._registry.mark_logging_ok(True)
            return True
        except Exception as exc:
            self._logger.exception(f"Logging initialization failed: {exc}")
            self._registry.mark_logging_ok(False)
            return False

    @measure_latency("metrics")
    def init_metrics(self, core_settings: CoreSettings) -> bool:
        """Start the Prometheus HTTP metrics server."""
        port = core_settings.quantum_metrics_port
        addr = core_settings.quantum_metrics_addr
        if port <= 0:
            self._registry.mark_metrics_http_ok(False)
            return False

        try:
            start_http_server(port, addr=addr)
            self._registry.mark_metrics_http_ok(True)
            return True
        except OSError as exc:
            self._logger.warning(f"Metrics HTTP server failed on {addr}:{port}: {exc}")
            self._registry.mark_metrics_http_ok(False)
            return False

    # --------------------------------------------------------------------------
    # Shutdown
    # --------------------------------------------------------------------------
    def shutdown_tracing(self, *, set_gauge_down: bool = True) -> None:
        """Gracefully shut down the tracing subsystem."""
        with suppress(Exception):
            detach_process_baggage_if_any()
        self._shutdown_tracing_if_any()
        if set_gauge_down:
            self._registry.mark_tracing_up(False)

    def shutdown_logging(self, *, set_gauge_down: bool = True) -> None:
        """Close all logging handlers and sinks."""
        with suppress(Exception):
            close_and_remove_all_handlers(logging.getLogger())
        if set_gauge_down:
            self._registry.mark_logging_sink_up(False)

    # --------------------------------------------------------------------------
    # Health & Utilities
    # --------------------------------------------------------------------------
    def probe_logging_sinks(self, *, deep_probe: bool = False) -> bool:
        """Probe all logging sinks for writability."""
        try:
            ok = self._probe_logging_sinks(deep_probe=deep_probe)
            self._registry.mark_logging_sink_up(ok)
            return ok
        except Exception as exc:
            self._logger.warning(f"Logging sinks probe failed: {exc}")
            self._registry.mark_logging_sink_up(False)
            return False

    @staticmethod
    def refresh_build_info() -> None:
        """Refresh build info metadata from environment variables."""
        with suppress(Exception):
            refresh_build_info_from_env()

    def reset_health(self) -> None:
        """Reset all Prometheus health gauges to zero."""
        self._registry.reset_all()
