from __future__ import annotations

import logging
import threading

from collections.abc import Iterator
from contextlib import contextmanager

from quantum.infrastructure.observability.bootstrap.lifecycle.configs.filesystem_probe_config import (
    FileSystemProbeConfig,
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
from quantum.infrastructure.observability.bootstrap.lifecycle.dependencies import (
    create_observability_dependencies,
)
from quantum.infrastructure.observability.bootstrap.lifecycle.lifecycle import (
    LifecycleService,
)
from quantum.infrastructure.observability.context.run_id import (
    generate_run_id,
    get_run_id,
)

_logger = logging.getLogger(__name__)


# ╭────────────────────────────────────────────────────────────────────────────╮
# │ Internal state                                                             │
# ╰────────────────────────────────────────────────────────────────────────────╯
_initialized = False
_init_lock = threading.Lock()

_lifecycle: LifecycleService | None = None
_dependencies = create_observability_dependencies()


# ╭────────────────────────────────────────────────────────────────────────────╮
# │ Public API                                                                 │
# ╰────────────────────────────────────────────────────────────────────────────╯
def init_observability(
    *,
    logging_config: LoggingConfig,
    tracing_config: TracingConfig,
    metrics_config: MetricsConfig,
    probe_config: FileSystemProbeConfig,
    force: bool = False,
) -> bool:
    """
    High-level initialization entry point for the Observability stack.

    This function does NOT load configuration:
      The caller (runtime or application entry point) must already have
      constructed the Value Objects through its own configuration logic.

    This ensures total separation from ConfigManager and makes this module
    fully Clean Architecture compliant.
    """
    global _initialized, _lifecycle

    with _init_lock:
        if _initialized and not force:
            _logger.debug("[Observability] Already initialized — skipping.")
            return True

        # Ensure a run_id exists for correlation context
        if not get_run_id():
            generate_run_id()

        if _lifecycle is None:
            _lifecycle = LifecycleService(_dependencies)

        ok = _lifecycle.initialize(
            logging_config=logging_config,
            tracing_config=tracing_config,
            metrics_config=metrics_config,
            probe_config=probe_config,
            force=force,
        )

        _initialized = ok
        return ok


def shutdown_observability(
    *,
    close_logging: bool = True,
    shutdown_tracing: bool = True,
    set_gauges_down: bool = False,
) -> None:
    """
    Clean shutdown of the entire observability pipeline.

    This version does NOT clear configuration caches because this module
    no longer touches ConfigManager or global config.
    """
    global _initialized, _lifecycle

    if _lifecycle is not None:
        _lifecycle.shutdown(
            close_logging=close_logging,
            shutdown_tracing=shutdown_tracing,
            set_gauges_down=set_gauges_down,
        )

    _initialized = False
    _logger.info("[Observability] Stack shutdown complete.")


@contextmanager
def observability_session(
    *,
    logging_config: LoggingConfig,
    tracing_config: TracingConfig,
    metrics_config: MetricsConfig,
    probe_config: FileSystemProbeConfig,
    force: bool = False,
) -> Iterator[None]:
    """Context manager for deterministic init/shutdown."""
    init_observability(
        logging_config=logging_config,
        tracing_config=tracing_config,
        metrics_config=metrics_config,
        probe_config=probe_config,
        force=force,
    )
    try:
        yield
    finally:
        shutdown_observability()
