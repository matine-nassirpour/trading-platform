import logging
import threading
from contextlib import contextmanager, suppress

from quantum.core.config.runtime.manager import ConfigManager
from quantum.infrastructure.observability.bootstrap.health_registry import (
    get_health_registry,
)
from quantum.infrastructure.observability.bootstrap.lifecycle import LifecycleService
from quantum.shared.context.run_id import generate_run_id, get_run_id

# ╭─────────────────────────────────────────────────────────────────────────────╮
# │ Internal state                                                              │
# ╰─────────────────────────────────────────────────────────────────────────────╯

_initialized = False
_init_lock = threading.Lock()
_logger = logging.getLogger(__name__)


# ╭─────────────────────────────────────────────────────────────────────────────╮
# │ Core API                                                                    │
# ╰─────────────────────────────────────────────────────────────────────────────╯
def init_observability(force: bool = False) -> None:
    """
    Thread-safe and idempotent initialization of the observability subsystems.
    """
    global _initialized

    with _init_lock:
        if _initialized and not force:
            return

        if force:
            with suppress(AttributeError):
                ConfigManager.clear_caches()

        # ─── Load configuration models
        core_settings = ConfigManager.load()
        logging_settings = ConfigManager.load_logging()
        tracing_settings = ConfigManager.load_tracing()

        # ─── Setup registry and lifecycle
        registry = get_health_registry()
        lifecycle = LifecycleService(registry)

        # ─── Reset all gauges (health state)
        registry.reset_all()
        lifecycle.refresh_build_info()

        # ─── Ensure run_id exists for correlation context
        if not get_run_id():
            generate_run_id()

        # ─── Initialize tracing
        tracing_ok = lifecycle.init_tracing(core_settings, tracing_settings, force)
        registry.mark_tracing_ok(tracing_ok)

        # ─── Initialize logging
        logging_ok = lifecycle.init_logging_safe(core_settings, logging_settings)
        registry.mark_logging_ok(logging_ok)

        # ─── Probe persistent sinks (deep probe optional)
        lifecycle.probe_logging_sinks(
            deep_probe=logging_settings.quantum_log_deep_probe
        )

        # ─── Initialize metrics HTTP exporter
        lifecycle.init_metrics(core_settings)

        # ─── Aggregate pipeline health
        pipeline_ok = tracing_ok and logging_ok
        registry.mark_pipeline_up(pipeline_ok)

        _initialized = pipeline_ok


def shutdown_observability(
    *,
    close_logging: bool = True,
    shutdown_tracing: bool = True,
    reset_state: bool = True,
    set_gauges_down: bool = False,
) -> None:
    """Clean and idempotent shutdown of observability components."""
    global _initialized

    registry = get_health_registry()
    lifecycle = LifecycleService(registry)

    if shutdown_tracing:
        lifecycle.shutdown_tracing(set_gauge_down=set_gauges_down)

    if close_logging:
        lifecycle.shutdown_logging(set_gauge_down=set_gauges_down)

    if set_gauges_down:
        registry.mark_pipeline_up(False)

    if reset_state:
        _initialized = False


@contextmanager
def observability_session(*, force: bool = False):
    """
    Context manager for automatic observability setup and teardown.

    Example:
        with observability_session():
            run_trading_pipeline()
    """
    init_observability(force=force)
    try:
        yield
    finally:
        shutdown_observability()
