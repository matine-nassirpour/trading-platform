from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from prometheus_client import Gauge


# ╭────────────────────────────────────────────────────────────────────────────╮
# │ Metrics bundle                                                             │
# ╰────────────────────────────────────────────────────────────────────────────╯
@dataclass(frozen=True)
class HealthMetrics:
    pipeline_up: Gauge
    tracing_up: Gauge
    logging_sink_up: Gauge
    logging_ok: Gauge
    tracing_ok: Gauge
    metrics_http_ok: Gauge


# ╭────────────────────────────────────────────────────────────────────────────╮
# │ Public interface for health reporting                                      │
# ╰────────────────────────────────────────────────────────────────────────────╯
class HealthMonitor(Protocol):
    """Interface for reporting observability subsystem health."""

    def mark_pipeline_up(self, ok: bool) -> None: ...
    def mark_tracing_up(self, ok: bool) -> None: ...
    def mark_logging_sink_up(self, ok: bool) -> None: ...
    def mark_logging_ok(self, ok: bool) -> None: ...
    def mark_tracing_ok(self, ok: bool) -> None: ...
    def mark_metrics_http_ok(self, ok: bool) -> None: ...
    def reset_all(self) -> None: ...


class HealthRegistry:
    """Pure health status manager using Prometheus Gauges + internal canonical state."""

    def __init__(self, metrics: HealthMetrics) -> None:
        self._m = metrics

        # Canonical internal state (source of truth)
        self._pipeline_up: bool = False
        self._tracing_up: bool = False
        self._logging_sink_up: bool = False
        self._logging_ok: bool = False
        self._tracing_ok: bool = False
        self._metrics_http_ok: bool = False

    # --------------------------------------------------------------------------
    # Public API - High level setters
    # --------------------------------------------------------------------------
    def mark_pipeline_up(self, ok: bool) -> None:
        self._pipeline_up = ok
        self._m.pipeline_up.set(1 if ok else 0)

    def mark_tracing_up(self, ok: bool) -> None:
        self._tracing_up = ok
        self._m.tracing_up.set(1 if ok else 0)

    def mark_logging_sink_up(self, ok: bool) -> None:
        self._logging_sink_up = ok
        self._m.logging_sink_up.set(1 if ok else 0)

    def mark_logging_ok(self, ok: bool) -> None:
        self._logging_ok = ok
        self._m.logging_ok.set(1 if ok else 0)

    def mark_tracing_ok(self, ok: bool) -> None:
        self._tracing_ok = ok
        self._m.tracing_ok.set(1 if ok else 0)

    def mark_metrics_http_ok(self, ok: bool) -> None:
        self._metrics_http_ok = ok
        self._m.metrics_http_ok.set(1 if ok else 0)

    # --------------------------------------------------------------------------
    # Public API — Getters (read from canonical state, never from Gauge)
    # --------------------------------------------------------------------------
    def is_pipeline_up(self) -> bool:
        return self._pipeline_up

    def is_tracing_up(self) -> bool:
        return self._tracing_up

    def is_logging_sink_up(self) -> bool:
        return self._logging_sink_up

    def is_logging_ok(self) -> bool:
        return self._logging_ok

    def is_tracing_ok(self) -> bool:
        return self._tracing_ok

    def is_metrics_http_ok(self) -> bool:
        return self._metrics_http_ok

    # --------------------------------------------------------------------------
    # Utilities
    # --------------------------------------------------------------------------
    def reset_all(self) -> None:
        """
        Reset all gauges to zero.
        Caller must ensure this is only invoked in a controlled lifecycle phase.
        """
        self.mark_pipeline_up(False)
        self.mark_tracing_up(False)
        self.mark_logging_sink_up(False)
        self.mark_logging_ok(False)
        self.mark_tracing_ok(False)
        self.mark_metrics_http_ok(False)


# ╭────────────────────────────────────────────────────────────────────────────╮
# │ Factory function                                                           │
# ╰────────────────────────────────────────────────────────────────────────────╯
def build_health_registry(prefix: str = "quantum") -> HealthRegistry:
    """
    Deterministic, factory for HealthRegistry + Gauges.

    This replaces all implicit singletons. It produces:
        - well-defined Prometheus gauge set
        - explicit namespacing (default: 'quantum')
        - fully isolated HealthRegistry instance
        - safe to call during composition
    """

    metrics = HealthMetrics(
        pipeline_up=Gauge(
            f"{prefix}_pipeline_up",
            "Indicates global observability pipeline health (1=up, 0=down)",
        ),
        tracing_up=Gauge(
            f"{prefix}_tracing_up",
            "Indicates tracing subsystem reachability (1=up, 0=down)",
        ),
        logging_sink_up=Gauge(
            f"{prefix}_logging_sink_up",
            "Indicates logging sink availability (1=up, 0=down)",
        ),
        logging_ok=Gauge(
            f"{prefix}_logging_ok",
            "Indicates successful logging initialization (1=ok, 0=failed)",
        ),
        tracing_ok=Gauge(
            f"{prefix}_tracing_ok",
            "Indicates successful tracing initialization (1=ok, 0=failed)",
        ),
        metrics_http_ok=Gauge(
            f"{prefix}_metrics_http_ok",
            "Indicates Prometheus exporter health (1=ok, 0=failed)",
        ),
    )

    return HealthRegistry(metrics)
