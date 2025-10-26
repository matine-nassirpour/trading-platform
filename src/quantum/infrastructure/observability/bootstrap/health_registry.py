from __future__ import annotations

import threading
from typing import Final

from prometheus_client import Gauge


class HealthRegistry:
    """
    Thread-safe registry encapsulating Prometheus Gauges
    that track subsystem-level health for observability.

    Each setter method directly updates a specific Gauge.

    Thread-safety:
        The class follows a double-checked locking singleton pattern.
        Access through `HealthRegistry.get_instance()` or `get_health_registry()`.
    """

    _instance_lock = threading.Lock()
    _instance: HealthRegistry | None = None

    # Gauge name constants
    PIPELINE_UP: Final[str] = "quantum_pipeline_up"
    OTEL_TRACING_UP: Final[str] = "quantum_otel_tracing_up"
    LOGGING_SINK_UP: Final[str] = "quantum_logging_sink_up"
    PIPELINE_LOGGING_OK: Final[str] = "quantum_pipeline_logging_ok"
    PIPELINE_TRACING_OK: Final[str] = "quantum_pipeline_tracing_ok"
    PIPELINE_METRICS_HTTP_OK: Final[str] = "quantum_pipeline_metrics_http_ok"

    def __init__(self) -> None:
        # ----------------------------------------------------------------------
        # Prometheus Gauges
        # ----------------------------------------------------------------------
        self.pipeline_up = Gauge(
            self.PIPELINE_UP,
            "Overall health of the observability pipeline (1=up, 0=down).",
        )

        self.otel_tracing_up = Gauge(
            self.OTEL_TRACING_UP,
            "OpenTelemetry tracing subsystem health (1=up, 0=down).",
        )

        self.logging_sink_up = Gauge(
            self.LOGGING_SINK_UP,
            "Health of logging persistent sinks (1=ok, 0=unwritable or missing).",
        )

        self.pipeline_logging_ok = Gauge(
            self.PIPELINE_LOGGING_OK,
            "Logging pipeline initialization status (1=success, 0=failure).",
        )

        self.pipeline_tracing_ok = Gauge(
            self.PIPELINE_TRACING_OK,
            "Tracing pipeline initialization status (1=success, 0=failure).",
        )

        self.pipeline_metrics_http_ok = Gauge(
            self.PIPELINE_METRICS_HTTP_OK,
            "Prometheus HTTP exporter availability (1=ok, 0=failed).",
        )

    # --------------------------------------------------------------------------
    # Public API - High level setters
    # --------------------------------------------------------------------------
    def mark_pipeline_up(self, ok: bool) -> None:
        self.pipeline_up.set(1 if ok else 0)

    def mark_tracing_up(self, ok: bool) -> None:
        self.otel_tracing_up.set(1 if ok else 0)

    def mark_logging_sink_up(self, ok: bool) -> None:
        self.logging_sink_up.set(1 if ok else 0)

    def mark_logging_ok(self, ok: bool) -> None:
        self.pipeline_logging_ok.set(1 if ok else 0)

    def mark_tracing_ok(self, ok: bool) -> None:
        self.pipeline_tracing_ok.set(1 if ok else 0)

    def mark_metrics_http_ok(self, ok: bool) -> None:
        self.pipeline_metrics_http_ok.set(1 if ok else 0)

    # --------------------------------------------------------------------------
    # Utilities
    # --------------------------------------------------------------------------
    def reset_all(self) -> None:
        """Reset all gauges to zero (used on forced reinit)."""
        self.pipeline_up.set(0)
        self.otel_tracing_up.set(0)
        self.logging_sink_up.set(0)
        self.pipeline_logging_ok.set(0)
        self.pipeline_tracing_ok.set(0)
        self.pipeline_metrics_http_ok.set(0)

    # --------------------------------------------------------------------------
    # Singleton access
    # --------------------------------------------------------------------------
    @classmethod
    def get_instance(cls) -> HealthRegistry:
        """Thread-safe singleton accessor."""
        if cls._instance is None:
            with cls._instance_lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance


# ╭────────────────────────────────────────────────────────────────────────────╮
# │ Module-Level Convenience Accessor                                          │
# ╰────────────────────────────────────────────────────────────────────────────╯
def get_health_registry() -> HealthRegistry:
    """
    Retrieve the global HealthRegistry instance.

    Example:
        hr = get_health_registry()
        hr.mark_pipeline_up(True)
    """
    return HealthRegistry.get_instance()
