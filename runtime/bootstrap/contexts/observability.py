from __future__ import annotations

import logging

from runtime.bootstrap.contexts.identity import RuntimeIdentityContext

from quantum.infrastructure.config.models.logging import LoggingSettings
from quantum.infrastructure.config.models.tracing import TracingSettings
from quantum.infrastructure.observability.bootstrap.init_manager import (
    init_observability,
    shutdown_observability,
)
from quantum.infrastructure.observability.bootstrap.lifecycle.configs.logging_config import (
    LoggingConfig,
)
from quantum.infrastructure.observability.bootstrap.lifecycle.configs.metrics_config import (
    MetricsConfig,
)
from quantum.infrastructure.observability.bootstrap.lifecycle.configs.tracing_config import (
    TracingConfig,
)

LOGGER = logging.getLogger("quantum.runtime.observability")


class RuntimeObservabilityContext:
    """
    Observability lifecycle controller.

    Responsibility:
    - Initialize observability subsystems
    - Shutdown observability deterministically
    - Maintain observability initialization state

    No business logic.
    No runtime policy.
    """

    def __init__(
        self,
        *,
        identity: RuntimeIdentityContext,
        logging_settings: LoggingSettings,
        tracing_settings: TracingSettings,
        metrics_host: str,
        metrics_port: int,
    ) -> None:
        self._identity = identity
        self._logging_settings = logging_settings
        self._tracing_settings = tracing_settings
        self._metrics_host = metrics_host
        self._metrics_port = metrics_port
        self._initialized = False

    # --------------------------------------------------------------------------
    # Internal adapters
    # --------------------------------------------------------------------------
    def _make_logging_config(self) -> LoggingConfig:
        s = self._logging_settings
        return LoggingConfig(
            identity=self._identity.identity,
            log_dir=s.quantum_log_dir.as_path(),
            audit_dir=s.quantum_audit_dir.as_path(),
            audit_allowlist=s.quantum_audit_allowlist,
            log_level=getattr(logging, s.quantum_log_level.upper(), logging.INFO),
            sample_info_every=s.quantum_log_sample_info,
            ratelimit_rps=float(s.quantum_log_rps),
            log_fsync=s.quantum_log_fsync,
            log_max_bytes=s.quantum_log_max_bytes,
            log_warn_bytes=s.quantum_log_warn_bytes,
        )

    def _make_tracing_config(self) -> TracingConfig:
        s = self._tracing_settings
        return TracingConfig(
            identity=self._identity.identity,
            trace_exporter=s.quantum_trace_exporter,
            trace_otlp_endpoint=s.quantum_trace_otlp_endpoint,
            trace_otlp_protocol=s.quantum_trace_otlp_protocol,
            trace_otlp_headers=s.quantum_trace_otlp_headers or "",
            trace_otlp_timeout_ms=s.quantum_trace_otlp_timeout_ms,
            trace_otlp_compression=s.quantum_trace_otlp_compression,
            trace_otlp_insecure=s.quantum_trace_otlp_insecure,
            trace_sample=s.quantum_trace_sample,
        )

    def _make_metrics_config(self) -> MetricsConfig:
        return MetricsConfig(
            host=self._metrics_host,
            port=self._metrics_port,
        )

    # --------------------------------------------------------------------------
    # Public API
    # --------------------------------------------------------------------------
    def initialize(self) -> bool:
        if self._initialized:
            return True

        try:
            ok = init_observability(
                logging_config=self._make_logging_config(),
                tracing_config=self._make_tracing_config(),
                metrics_config=self._make_metrics_config(),
                force=False,
            )
            self._initialized = ok
            return ok
        except Exception as exc:
            LOGGER.exception("Observability initialization failed: %s.", exc)
            return False

    def shutdown(self) -> None:
        if not self._initialized:
            return

        try:
            shutdown_observability(
                close_logging=True,
                shutdown_tracing=True,
                set_gauges_down=True,
            )
        finally:
            self._initialized = False
