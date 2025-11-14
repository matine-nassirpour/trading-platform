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
    """Pure health status manager using an injected set of Prometheus Gauges."""

    def __init__(self, metrics: HealthMetrics) -> None:
        self._m = metrics

    # --------------------------------------------------------------------------
    # Public API - High level setters
    # --------------------------------------------------------------------------
    def mark_pipeline_up(self, ok: bool) -> None:
        self._m.pipeline_up.set(1 if ok else 0)

    def mark_tracing_up(self, ok: bool) -> None:
        self._m.tracing_up.set(1 if ok else 0)

    def mark_logging_sink_up(self, ok: bool) -> None:
        self._m.logging_sink_up.set(1 if ok else 0)

    def mark_logging_ok(self, ok: bool) -> None:
        self._m.logging_ok.set(1 if ok else 0)

    def mark_tracing_ok(self, ok: bool) -> None:
        self._m.tracing_ok.set(1 if ok else 0)

    def mark_metrics_http_ok(self, ok: bool) -> None:
        self._m.metrics_http_ok.set(1 if ok else 0)

    # --------------------------------------------------------------------------
    # Utilities
    # --------------------------------------------------------------------------
    def reset_all(self) -> None:
        """
        Reset all gauges to zero.
        Caller must ensure this is only invoked in a controlled lifecycle phase.
        """
        self._m.pipeline_up.set(0)
        self._m.tracing_up.set(0)
        self._m.logging_sink_up.set(0)
        self._m.logging_ok.set(0)
        self._m.tracing_ok.set(0)
        self._m.metrics_http_ok.set(0)
