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
from functools import wraps
from typing import Any, Final

from prometheus_client import Counter, Histogram

_logger = logging.getLogger(__name__)


class BootstrapDiagnostics:
    """
    Tracks internal metrics about the observability bootstrap lifecycle.
    """

    _instance_lock = threading.Lock()
    _instance: BootstrapDiagnostics | None = None

    # Prometheus metric names
    _LATENCY_METRIC: Final[str] = "quantum_observability_init_duration_seconds"
    _FAILURE_METRIC: Final[str] = "quantum_observability_init_failures_total"

    def __init__(self) -> None:
        # ---------------------------------------------------------------------
        # Prometheus metrics
        # ---------------------------------------------------------------------
        self._latency_hist = Histogram(
            self._LATENCY_METRIC,
            "Initialization duration of observability subsystems (seconds).",
            labelnames=("subsystem",),
            buckets=(0.01, 0.05, 0.1, 0.25, 0.5, 1, 2, 5, 10),
        )

        self._failure_counter = Counter(
            self._FAILURE_METRIC,
            "Count of failed subsystem initializations.",
            labelnames=("subsystem",),
        )

        # Internal registry of diagnostic results (for reporting)
        self._results: dict[str, float] = {}
        self._failures: set[str] = set()

    # -------------------------------------------------------------------------
    # Singleton Access
    # -------------------------------------------------------------------------
    @classmethod
    def get_instance(cls) -> BootstrapDiagnostics:
        if cls._instance is None:
            with cls._instance_lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    # -------------------------------------------------------------------------
    # Metrics Recording
    # -------------------------------------------------------------------------
    def record_init_latency(self, subsystem: str, duration: float) -> None:
        """Record initialization latency for a subsystem."""
        self._latency_hist.labels(subsystem=subsystem).observe(duration)
        self._results[subsystem] = duration
        _logger.debug(f"[Diagnostics] {subsystem} init in {duration:.3f}s")

    def record_failure(self, subsystem: str) -> None:
        """Increment failure count for a subsystem."""
        self._failure_counter.labels(subsystem=subsystem).inc()
        self._failures.add(subsystem)
        _logger.warning(f"[Diagnostics] {subsystem} initialization failed")

    def get_summary_report(self) -> dict[str, Any]:
        """Return a structured summary of recorded diagnostics."""
        return {
            "latencies": dict(self._results),
            "failures": list(self._failures),
        }


# ╭───────────────────────────────────────────────────────────────────────────╮
# │ Decorator for automatic instrumentation                                   │
# ╰───────────────────────────────────────────────────────────────────────────╯
def measure_latency(subsystem_name: str) -> Callable[..., Any]:
    """
    Decorator to measure and record initialization latency for a subsystem.

    Example:
        @measure_latency("logging")
        def init_logging(...):
            ...
    """

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            diagnostics = BootstrapDiagnostics.get_instance()
            start = time.perf_counter()
            try:
                result = func(*args, **kwargs)
                return result
            except Exception:
                diagnostics.record_failure(subsystem_name)
                raise
            finally:
                duration = time.perf_counter() - start
                diagnostics.record_init_latency(subsystem_name, duration)

        return wrapper

    return decorator


# ╭───────────────────────────────────────────────────────────────────────────╮
# │ Convenience Accessor                                                      │
# ╰───────────────────────────────────────────────────────────────────────────╯
def get_diagnostics() -> BootstrapDiagnostics:
    """Retrieve the global BootstrapDiagnostics instance."""
    return BootstrapDiagnostics.get_instance()
