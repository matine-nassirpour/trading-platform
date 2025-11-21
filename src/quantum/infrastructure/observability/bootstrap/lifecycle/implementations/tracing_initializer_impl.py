from __future__ import annotations

import logging

from typing import Any, Final

from quantum.infrastructure.observability.bootstrap.lifecycle.configs.tracing_config import (
    TracingConfig,
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
        # TracerProvider Creation
        provider = init_tracing(
            core_settings=dict(
                quantum_env=config.environment,
                quantum_ns=config.service_namespace,
                quantum_app_name=config.service_name,
                quantum_app_version=config.service_version,
                quantum_instance_id=config.instance_id,
            ),
            tracing_settings=dict(
                quantum_trace_exporter=config.exporter_type,
                quantum_trace_endpoint=config.exporter_endpoint,
                quantum_trace_sample=config.sample_ratio,
            ),
            force=True,
        )

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
