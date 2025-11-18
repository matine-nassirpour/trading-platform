"""
Diagnostics Module
──────────────────

Provides self-observation of the observability stack itself:
- Measures initialization latencies for subsystems
- Records success/failure counts
- Exposes Prometheus metrics for internal performance tracking
"""

from __future__ import annotations

import logging
import threading
import time

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, Final

from prometheus_client import Counter, Histogram

LOGGER: Final = logging.getLogger(__name__)


# ╭────────────────────────────────────────────────────────────────────────────╮
# │ Metrics bundle                                                             │
# ╰────────────────────────────────────────────────────────────────────────────╯
@dataclass(frozen=True)
class DiagnosticsMetrics:
    latency_hist: Histogram
    failure_counter: Counter


class BootstrapDiagnostics:
    """
    Pure diagnostics manager, responsible for recording:
      - subsystem initialization latency
      - subsystem initialization failures

    All storage and metrics updates are thread-safe.
    """

    def __init__(self, metrics: DiagnosticsMetrics) -> None:
        self._metrics = metrics
        self._lock = threading.Lock()
        self._results: dict[str, float] = {}
        self._failures: set[str] = set()

    # --------------------------------------------------------------------------
    # Public API
    # --------------------------------------------------------------------------
    def record_init_latency(self, subsystem: str, duration: float) -> None:
        self._metrics.latency_hist.labels(subsystem=subsystem).observe(duration)
        with self._lock:
            self._results[subsystem] = duration
        LOGGER.debug(f"[Diagnostics] {subsystem} init in {duration:.3f}s")

    def record_failure(self, subsystem: str) -> None:
        self._metrics.failure_counter.labels(subsystem=subsystem).inc()
        with self._lock:
            self._failures.add(subsystem)
        LOGGER.warning(f"[Diagnostics] {subsystem} initialization failed")

    def get_summary_report(self) -> dict[str, Any]:
        with self._lock:
            return {
                "latencies": dict(self._results),
                "failures": list(self._failures),
            }


# ╭────────────────────────────────────────────────────────────────────────────╮
# │ Decorator factory                                                          │
# ╰────────────────────────────────────────────────────────────────────────────╯
def make_latency_decorator(
    diagnostics: BootstrapDiagnostics,
) -> Callable[[str], Callable[..., Any]]:
    """
    Factory producing a latency-measuring decorator tied to a specific
    diagnostics instance (no globals).
    """

    def measure_latency(subsystem_name: str) -> Callable[..., Any]:
        def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
            def wrapper(*args: Any, **kwargs: Any) -> Any:
                start = time.perf_counter()
                try:
                    return func(*args, **kwargs)
                except Exception:
                    diagnostics.record_failure(subsystem_name)
                    raise
                finally:
                    duration = time.perf_counter() - start
                    diagnostics.record_init_latency(subsystem_name, duration)

            return wrapper

        return decorator

    return measure_latency
