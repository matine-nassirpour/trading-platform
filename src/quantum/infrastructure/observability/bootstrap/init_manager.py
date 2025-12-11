from __future__ import annotations

import logging
import threading

from collections.abc import Iterator
from contextlib import contextmanager
from typing import Final

from quantum.infrastructure.observability.bootstrap.lifecycle.configs.logging_config import (
    LoggingConfig,
)
from quantum.infrastructure.observability.bootstrap.lifecycle.configs.metrics_config import (
    MetricsConfig,
)
from quantum.infrastructure.observability.bootstrap.lifecycle.configs.tracing_config import (
    TracingConfig,
)
from quantum.infrastructure.observability.bootstrap.lifecycle.dependencies import (
    create_observability_dependencies,
)
from quantum.infrastructure.observability.context.context_attributes_provider import (
    ContextAttributesProvider,
)
from quantum.infrastructure.observability.context.run_id import generate_run_id
from quantum.infrastructure.observability.runtime.runtime_context import (
    _RuntimeContextHolder,
)

LOGGER: Final = logging.getLogger(__name__)
_init_lock = threading.Lock()


# ╭────────────────────────────────────────────────────────────────────────────╮
# │ Public API                                                                 │
# ╰────────────────────────────────────────────────────────────────────────────╯
def init_observability(
    *,
    logging_config: LoggingConfig,
    tracing_config: TracingConfig,
    metrics_config: MetricsConfig,
    force: bool = False,
) -> bool:
    """
    Deterministic initialization entrypoint for the Observability stack.

    Responsibilities:
        • Ensures run_id exists
        • Installs ObservabilityRuntimeContext once (composition root)
        • Delegates init to LifecycleService
        • No global mutable state → certifiable + testable

    Returns:
        bool — True if pipeline is operational, False otherwise.
    """
    deps = create_observability_dependencies()

    with _init_lock:
        # Ensure a run_id exists for correlation context
        ctx = ContextAttributesProvider.get()
        if ctx.run_id is None:
            generate_run_id()

        # Install immutable runtime context exactly once
        _RuntimeContextHolder.install(deps=deps)

        # Perform initialization through deterministic LifecycleService
        runtime_ctx = _RuntimeContextHolder.get()

        ok = runtime_ctx.lifecycle.initialize(
            logging_config=logging_config,
            tracing_config=tracing_config,
            metrics_config=metrics_config,
            force=force,
        )

        return ok


def shutdown_observability(
    *,
    close_logging: bool = True,
    shutdown_tracing: bool = True,
    set_gauges_down: bool = False,
) -> None:
    """
    Clean shutdown of the entire observability pipeline.
    """
    try:
        runtime_ctx = _RuntimeContextHolder.get()
    except RuntimeError:
        return

    runtime_ctx.lifecycle.shutdown(
        close_logging=close_logging,
        shutdown_tracing=shutdown_tracing,
        set_gauges_down=set_gauges_down,
    )
    LOGGER.info("[Observability] Shutdown complete.")


@contextmanager
def observability_session(
    *,
    logging_config: LoggingConfig,
    tracing_config: TracingConfig,
    metrics_config: MetricsConfig,
    force: bool = False,
) -> Iterator[None]:
    """High-level deterministic context manager."""
    init_observability(
        logging_config=logging_config,
        tracing_config=tracing_config,
        metrics_config=metrics_config,
        force=force,
    )
    try:
        yield
    finally:
        shutdown_observability()
