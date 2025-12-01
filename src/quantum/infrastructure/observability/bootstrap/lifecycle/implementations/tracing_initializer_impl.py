from __future__ import annotations

import logging

from typing import Any, Final

from quantum.infrastructure.observability.bootstrap.lifecycle.configs.tracing_config import (
    TracingConfig,
)
from quantum.infrastructure.observability.foundation.config.tracing_runtime_bundle import (
    TracingRuntimeBundle,
)
from quantum.infrastructure.observability.tracing.propagation import (
    detach_process_baggage_if_any,
    install_process_baggage,
    setup_propagation,
)
from quantum.infrastructure.observability.tracing.provider import init_tracing

LOGGER: Final = logging.getLogger(__name__)


class TracingInitializerImpl:
    """
    Concrete implementation of TracingInitializer for OpenTelemetry.

    Bridges the clean-architecture Value Object with the actual tracing system.
    """

    def __init__(self) -> None:
        self._provider: Any | None = None

    def initialize(self, config: TracingConfig) -> Any:
        bundle = TracingRuntimeBundle(
            identity=config.identity,
            trace_exporter=config.trace_exporter,
            trace_otlp_endpoint=config.trace_otlp_endpoint,
            trace_otlp_protocol=config.trace_otlp_protocol,
            trace_otlp_headers=config.trace_otlp_headers,
            trace_otlp_timeout_ms=config.trace_otlp_timeout_ms,
            trace_otlp_compression=config.trace_otlp_compression,
            trace_otlp_insecure=config.trace_otlp_insecure,
            trace_sample=config.trace_sample,
        )

        provider = init_tracing(bundle, replace_existing=True)

        setup_propagation()
        install_process_baggage()

        self._provider = provider
        return provider

    def shutdown(self) -> None:
        try:
            detach_process_baggage_if_any()
        except Exception as exc:
            LOGGER.debug(
                "Failed to detach process baggage during tracing shutdown: %s",
                exc,
            )

        if self._provider is not None:
            shutdown_fn = getattr(self._provider, "shutdown", None)
            if callable(shutdown_fn):
                try:
                    shutdown_fn(timeout=None)
                except Exception as exc:
                    LOGGER.debug(
                        "Tracing shutdown function failed: %s",
                        exc,
                    )

        self._provider = None
