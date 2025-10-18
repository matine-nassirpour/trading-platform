import logging
import os
import threading
from contextlib import contextmanager, suppress
from pathlib import Path

from prometheus_client import start_http_server

from quantum.infrastructure.observability.logging.logs import (
    close_and_remove_all_handlers,
    init_logging,
)
from quantum.infrastructure.observability.metrics.health import (
    logging_sink_up,
    otel_tracing_up,
    pipeline_logging_ok,
    pipeline_metrics_http_ok,
    pipeline_tracing_ok,
    pipeline_up,
    refresh_build_info_from_env,
)
from quantum.infrastructure.observability.tracing.propagation import (
    detach_process_baggage_if_any,
    install_process_baggage,
    setup_propagation,
)
from quantum.infrastructure.observability.tracing.traces import (
    TracingConfig,
    init_tracing,
)
from quantum.shared.config.config_manager import ConfigManager, Settings
from quantum.shared.config.observability_settings import ObservabilitySettings
from quantum.shared.context.run_id import generate_run_id, get_run_id

# ──────────────────────────────────────────────────────────────────────────────
# Internal state
# ──────────────────────────────────────────────────────────────────────────────

_initialized = False
_init_lock = threading.Lock()
_tracer_provider_ref: object | None = None

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────


def _iter_persistent_handlers() -> list[logging.Handler]:
    """Return all logging handlers with a 'base_dir' (persistent sinks)."""
    handlers: list[logging.Handler] = []
    root = logging.getLogger()
    handlers.extend([h for h in root.handlers if getattr(h, "base_dir", None)])
    audit_logger = logging.getLogger("quantum.trading")
    handlers.extend([h for h in audit_logger.handlers if getattr(h, "base_dir", None)])
    return handlers


def _probe_path_writable(
    base_dir: str | os.PathLike[str], deep_probe: bool = False
) -> bool:
    """Check directory writability; optionally perform deep write probe."""
    try:
        os.makedirs(base_dir, exist_ok=True)
        if not os.access(base_dir, os.W_OK):
            return False

        if deep_probe:
            base = Path(base_dir)
            probe = base / "__probe__/yyyy/mm/dd/hh"
            probe.mkdir(parents=True, exist_ok=True)
            f = probe / "probe.jsonl"
            with open(f, "a", encoding="utf-8") as fp:
                fp.write("{}\n")
            f.unlink(missing_ok=True)
            with suppress(OSError):
                probe.rmdir()
        return True
    except OSError:
        return False


def _probe_logging_sinks(deep_probe: bool = False) -> bool:
    """Return True if at least one persistent sink is writable."""
    persistent_handlers = _iter_persistent_handlers()
    if not persistent_handlers:
        return False
    return any(
        _probe_path_writable(getattr(h, "base_dir", ""), deep_probe=deep_probe)
        for h in persistent_handlers
        if getattr(h, "base_dir", None)
    )


def _shutdown_tracing_if_any() -> None:
    """Best-effort shutdown of previous tracer provider."""
    global _tracer_provider_ref
    tp = _tracer_provider_ref
    if tp is None:
        return
    shutdown = getattr(tp, "shutdown", None)
    if callable(shutdown):
        try:
            shutdown()
        except Exception as e:
            logger.debug(f"Tracer shutdown failed: {e}")
    _tracer_provider_ref = None


# ──────────────────────────────────────────────────────────────────────────────
# Init Subsystems
# ──────────────────────────────────────────────────────────────────────────────


def _init_tracing(
    settings: Settings,
    force: bool,
) -> bool:
    """Initialize OpenTelemetry tracing subsystem."""
    try:
        _shutdown_tracing_if_any()
        tp = init_tracing(
            TracingConfig(
                service_name=settings.quantum_app_name,
                environment=settings.quantum_env,
                namespace=settings.quantum_ns,
                exporter=settings.quantum_trace_exporter,
                sample_ratio=settings.quantum_trace_sample,
            ),
            replace_existing=force,
        )
        setup_propagation()
        install_process_baggage()
        otel_tracing_up.set(1)
        global _tracer_provider_ref
        _tracer_provider_ref = tp
        return True
    except Exception as e:
        logger.exception(f"Tracing initialization failed: {e}")
        otel_tracing_up.set(0)
        # Fallback (retry once)
        try:
            tp = init_tracing(
                TracingConfig(
                    service_name=settings.quantum_app_name,
                    environment=settings.quantum_env,
                    namespace=settings.quantum_ns,
                    exporter="none",
                    sample_ratio=0.0,
                )
            )
            setup_propagation()
            install_process_baggage()
            otel_tracing_up.set(1)
            _tracer_provider_ref = tp
            logger.warning(
                "Tracing fallback activated: exporter=none, sample_ratio=0.0"
            )
            return True
        except Exception as e2:
            logger.exception(f"Tracing fallback failed: {e2}")
            otel_tracing_up.set(0)
            return False


def _init_logging_safe(
    settings: Settings, observability: ObservabilitySettings
) -> bool:
    """Wrapper for logging initialization (safe)."""
    try:
        init_logging(settings, observability)
        return True
    except Exception as e:
        logger.exception(f"Logging initialization failed: {e}")
        return False


def _init_metrics(settings: Settings) -> bool:
    port = settings.quantum_metrics_port
    addr = settings.quantum_metrics_addr
    if port > 0:
        try:
            start_http_server(port, addr=addr)
            pipeline_metrics_http_ok.set(1)
            return True
        except OSError as e:
            logger.warning(f"Metrics HTTP server failed to start on {addr}:{port}: {e}")
            pipeline_metrics_http_ok.set(0)
            return False
    else:
        pipeline_metrics_http_ok.set(0)
        return False


# ──────────────────────────────────────────────────────────────────────────────
# Core API
# ──────────────────────────────────────────────────────────────────────────────


def init_observability(
    force: bool = False,
) -> None:
    """
    Idempotent and thread-safe bootstrap for observability.
    Initializes tracing, logging, and metrics with validated config.
    """
    global _initialized

    if force:
        with suppress(AttributeError):
            ConfigManager.clear_caches()

    with _init_lock:
        settings = ConfigManager.load()
        obs_settings = ConfigManager.load_observability()

        if _initialized and not force:
            return

        # Reset health gauges
        for g in (
            pipeline_up,
            otel_tracing_up,
            logging_sink_up,
            pipeline_logging_ok,
            pipeline_tracing_ok,
            pipeline_metrics_http_ok,
        ):
            with suppress(Exception):
                g.set(0)

        with suppress(Exception):
            refresh_build_info_from_env()

        if not get_run_id():
            generate_run_id()

        # ─── Initialize tracing
        tracing_ok = _init_tracing(settings, force)
        pipeline_tracing_ok.set(1 if tracing_ok else 0)

        # ─── Initialize logging
        if force:
            close_and_remove_all_handlers(logging.getLogger())
        logging_ok = _init_logging_safe(settings, obs_settings)
        pipeline_logging_ok.set(1 if logging_ok else 0)

        # ─── Probe sinks
        try:
            sinks_ok = _probe_logging_sinks(
                deep_probe=obs_settings.quantum_log_deep_probe
            )
        except Exception as e:
            logger.warning(f"Logging sinks probe failed: {e}")
            sinks_ok = False
        logging_sink_up.set(1 if sinks_ok else 0)

        # ─── Initialize metrics
        _init_metrics(settings)

        ok = logging_ok and tracing_ok
        pipeline_up.set(1 if ok else 0)
        _initialized = ok


def shutdown_observability(
    *,
    close_logging: bool = True,
    shutdown_tracing: bool = True,
    reset_state: bool = True,
    set_gauges_down: bool = False,
) -> None:
    """Clean and idempotent shutdown of observability components."""
    global _initialized

    if shutdown_tracing:
        try:
            detach_process_baggage_if_any()
        finally:
            _shutdown_tracing_if_any()
            if set_gauges_down:
                with suppress(Exception):
                    otel_tracing_up.set(0)

    if close_logging:
        try:
            close_and_remove_all_handlers(logging.getLogger())
        finally:
            if set_gauges_down:
                with suppress(Exception):
                    logging_sink_up.set(0)

    if set_gauges_down:
        with suppress(Exception):
            pipeline_up.set(0)

    if reset_state:
        _initialized = False


@contextmanager
def observability_session(*, force: bool = False):
    """Context manager for automatic observability setup/teardown."""
    init_observability(force=force)
    try:
        yield
    finally:
        shutdown_observability()
