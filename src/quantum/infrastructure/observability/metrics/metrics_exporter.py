from __future__ import annotations

from prometheus_client import Counter as PrometheusCounter

from quantum.infrastructure.observability.logging.core.diagnostics import (
    get_diagnostic_logger,
)
from quantum.infrastructure.observability.logging.core.metrics import _internal_metrics

_logger = get_diagnostic_logger()


class MetricsExporter:
    """
    C2 layer: binds internal C0 counters to external backends (e.g. Prometheus).

    This module never participates in the logging pipeline and never creates cycles.
    It is safe to call multiple times; bindings are idempotent and overwrite
    previous exporters cleanly.
    """

    def __init__(self) -> None:
        self._prom_counters: dict[str, PrometheusCounter] = {}

    # --------------------------------------------------------------------------
    # Public API
    # --------------------------------------------------------------------------
    def attach_prometheus_counter(
        self, internal_name: str, prom_name: str, help_text: str
    ) -> None:
        """
        Bind a C0 internal counter to a Prometheus counter.
        Calling C0Counter.inc() will increment the bound Prometheus metric.

        Args:
            internal_name: name of the C0 counter (e.g. "schema_validation_errors")
            prom_name: name of the Prometheus metric (e.g. "logging_schema_validation_errors_total")
            help_text: Prometheus metric description
        """
        try:
            internal_counter = _internal_metrics.get(internal_name)
            if internal_counter is None:
                _logger.error(
                    f"[metrics-exporter] Unknown internal counter '{internal_name}'"
                )
                return

            # Create or reuse Prometheus metric
            if prom_name not in self._prom_counters:
                self._prom_counters[prom_name] = PrometheusCounter(prom_name, help_text)

            prom_counter = self._prom_counters[prom_name]

            # Bind: each internal counter's _inc becomes the Prometheus `.inc`
            def prom_inc(amount: int = 1) -> None:
                try:
                    prom_counter.inc(amount)
                except Exception as exc:
                    _logger.error(
                        f"[metrics-exporter] Prometheus increment failed for '{prom_name}': {exc.__class__.__name__}"
                    )

            internal_counter._inc = prom_inc

        except Exception as exc:
            _logger.error(
                f"[metrics-exporter] attach_prometheus_counter failed: {exc.__class__.__name__}"
            )

    # --------------------------------------------------------------------------
    # Helpers
    # --------------------------------------------------------------------------
    def bind_default_logging_metrics(self) -> None:
        """
        Convenient helper: binds the most common logging-related internal counters
        to Prometheus metrics using canonical names.
        """
        self.attach_prometheus_counter(
            "schema_validation_errors",
            "logging_schema_validation_errors_total",
            "Number of schema validation errors in the structured logging pipeline",
        )

        self.attach_prometheus_counter(
            "redactions",
            "logging_redactions_total",
            "Number of log redactions performed",
        )

        self.attach_prometheus_counter(
            "disk_errors",
            "logging_disk_errors_total",
            "Number of disk-related errors for log handlers",
        )


# Singleton instance — optional but convenient
metrics_exporter = MetricsExporter()
