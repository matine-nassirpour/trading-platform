from __future__ import annotations

from prometheus_client import Counter as PrometheusCounter

from quantum.infrastructure.observability.foundation.metrics.c0_metric_registry import (
    get_internal_counter,
)
from quantum.infrastructure.observability.foundation.system_diagnostics.c0_diagnostic_logger import (
    get_diagnostic_logger,
)

_logger = get_diagnostic_logger()


class MetricsExporter:
    """
    C2 layer: binds internal C0 counters to external backends (e.g. Prometheus).

    This module never participates in the logging pipeline and never creates cycles.
    It is safe to call multiple times; bindings are idempotent and overwrite
    previous exporters cleanly.
    """

    def __init__(self) -> None:
        # Cache of Prometheus counters to ensure idempotence
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
            internal_counter = get_internal_counter(internal_name)
            if internal_counter is None:
                _logger.error(
                    f"[metrics-exporter] Unknown internal counter '{internal_name}'"
                )
                return

            # Create or reuse the Prometheus counter
            if prom_name not in self._prom_counters:
                self._prom_counters[prom_name] = PrometheusCounter(prom_name, help_text)

            prom_counter = self._prom_counters[prom_name]

            # Hook executed on each increment from C0
            def prom_inc(amount: int = 1) -> None:
                try:
                    prom_counter.inc(amount)
                except Exception as exc:
                    _logger.error(
                        f"[metrics-exporter] Prometheus increment failed "
                        f"for '{prom_name}': {exc.__class__.__name__}"
                    )

            # Register this hook with the internal C0 counter
            internal_counter.bind_increment_hook(prom_inc)

        except Exception as exc:
            _logger.error(
                f"[metrics-exporter] attach_prometheus_counter failed: {exc.__class__.__name__}"
            )

    def bind_default_logging_metrics(self) -> None:
        """
        Bind ALL defined C0 logging counters to Prometheus metrics.
        This guarantees:
        - full coverage
        - deterministic naming
        - certifiable mapping table
        - future-safe extensibility
        """

        mapping = {
            # Logging pipeline
            "logging_pipeline_step_failures": (
                "logging_pipeline_step_failures_total",
                "Number of failures inside logging pipeline steps",
            ),
            # Redactions
            "logging_redactions_total": (
                "logging_redactions_total",
                "Number of redactions performed in structured logging",
            ),
            # Disk errors (partitioned logs)
            "logging_disk_errors": (
                "logging_disk_errors_total",
                "Number of disk errors in partitioned log handler",
            ),
            # File rotations
            "logging_file_rotations": (
                "logging_file_rotations_total",
                "Number of log file rotations for partitioned JSONL handler",
            ),
            # Audit channel
            "audit_disk_errors": (
                "audit_disk_errors_total",
                "Number of disk errors during audit event writes",
            ),
            "audit_events_written": (
                "audit_events_written_total",
                "Number of audit events written successfully",
            ),
        }

        for internal_name, (prom_name, help_text) in mapping.items():
            self.attach_prometheus_counter(
                internal_name=internal_name,
                prom_name=prom_name,
                help_text=help_text,
            )


# Singleton instance — optional but convenient
metrics_exporter = MetricsExporter()
