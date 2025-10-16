import logging
import os
import threading
from contextlib import contextmanager, suppress
from pathlib import Path
from typing import Literal

from prometheus_client import start_http_server

from quantum.infrastructure.observability.logging.logs import (
    LoggingConfig,
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
from quantum.shared.config.config_manager import ConfigManager
from quantum.shared.config.env_flags import get_bool
from quantum.shared.context.run_id import generate_run_id, get_run_id

# ──────────────────────────────────────────────────────────────────────────────
# Internal state
# ──────────────────────────────────────────────────────────────────────────────

_initialized = False
_init_lock = threading.Lock()
_metrics_httpd_started = False
_tracer_provider_ref: object | None = None

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────


def _iter_persistent_handlers() -> list[logging.Handler]:
    """
    Return all logging handlers that expose a 'base_dir' attribute,
    i.e. persistent sinks (partitioned JSONL or audit sinks).
    """
    handlers: list[logging.Handler] = []
    root = logging.getLogger()
    handlers.extend([h for h in root.handlers if getattr(h, "base_dir", None)])
    audit_logger = logging.getLogger("quantum.trading")
    handlers.extend([h for h in audit_logger.handlers if getattr(h, "base_dir", None)])
    return handlers


def _probe_path_writable(base_dir: str | os.PathLike[str]) -> bool:
    """
    Checks that a directory is writable. If QUANTUM_LOG_DEEP_PROBE=1,
    attempts a minimal write/read and cleanup.
    """
    try:
        os.makedirs(base_dir, exist_ok=True)
        if not os.access(base_dir, os.W_OK):
            return False

        if get_bool("QUANTUM_LOG_DEEP_PROBE", default=False):
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


def _probe_logging_sinks() -> bool:
    """
    Return True if at least one persistent sink is writable.
    Return False if no persistent sink is configured or writable.
    """
    persistent_handlers = _iter_persistent_handlers()
    if not persistent_handlers:
        return False

    any_writable = False
    for h in persistent_handlers:
        base_dir = getattr(h, "base_dir", None)
        if not base_dir:
            continue
        if _probe_path_writable(base_dir):
            any_writable = True
    return any_writable


def _shutdown_tracing_if_any() -> None:
    """Best effort shutdown of previous tracer provider (if any)."""
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
    app_name: str,
    env: str,
    ns: str,
    exporter: Literal["otlp", "console", "none"],
    force: bool,
    sample_ratio: float | None,
) -> bool:
    try:
        _shutdown_tracing_if_any()
        tp = init_tracing(
            TracingConfig(
                service_name=app_name,
                environment=env,
                namespace=ns,
                exporter=exporter,
                sample_ratio=sample_ratio,
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
                    service_name=app_name,
                    environment=env,
                    namespace=ns,
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


def _init_logging(
    app_name: str, env: str, ns: str, log_lvl: str, app_version: str
) -> bool:
    try:
        init_logging(
            LoggingConfig(
                app_name=app_name,
                environment=env,
                namespace=ns,
                log_level=log_lvl,
                app_version=app_version,
            )
        )
        return True
    except Exception as e:
        logger.exception(f"Logging initialization failed: {e}")
        return False


def _init_metrics(port: int, addr: str) -> bool:
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
    app_name: str | None = None,
    environment: str | None = None,
    namespace: str | None = None,
    log_level: str | None = None,
    sample_ratio: float | None = None,
    *,
    force: bool = False,
) -> None:
    """Idempotent + thread-safe observability bootstrap."""
    global _initialized

    if force:
        with suppress(AttributeError):
            ConfigManager.clear_caches()

    settings = ConfigManager.load()
    obs_settings = ConfigManager.load_observability()

    with _init_lock:
        if _initialized and not force:
            return

        # Reset health gauges
        pipeline_up.set(0)
        otel_tracing_up.set(0)
        logging_sink_up.set(0)
        pipeline_logging_ok.set(0)
        pipeline_tracing_ok.set(0)
        pipeline_metrics_http_ok.set(0)

        with suppress(Exception):
            refresh_build_info_from_env()

        if not get_run_id():
            generate_run_id()

        app_name = app_name or settings.quantum_app_name
        environment = environment or settings.quantum_env
        namespace = namespace or settings.quantum_ns
        log_level = log_level or obs_settings.quantum_log_level
        sample_ratio = (
            settings.quantum_trace_sample if sample_ratio is None else sample_ratio
        )
        app_version = settings.quantum_app_version

        if force:
            close_and_remove_all_handlers(logging.getLogger())

        # ─── Tracing - must be first
        exporter: Literal["otlp", "console", "none"] = settings.quantum_trace_exporter
        tracing_ok = _init_tracing(
            app_name, environment, namespace, exporter, force, sample_ratio
        )
        pipeline_tracing_ok.set(1 if tracing_ok else 0)

        # ─── Logging - must come after tracing
        logging_ok = _init_logging(
            app_name, environment, namespace, log_level, app_version
        )
        pipeline_logging_ok.set(1 if logging_ok else 0)

        # Persistent sinks up? (partition and/or audit)
        try:
            sinks_ok = _probe_logging_sinks()
        except Exception as e:
            logger.warning(f"Logging sinks probe failed: {e}")
            sinks_ok = False

        logging_sink_up.set(1 if sinks_ok else 0)

        # ─── Metrics HTTP endpoint
        port = settings.quantum_metrics_port
        addr = settings.quantum_metrics_addr
        _init_metrics(port, addr)

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
    """
    Clean and idempotent shutdown of observability components.
    """
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
def observability_session(
    app_name: str | None = None,
    environment: str | None = None,
    namespace: str | None = None,
    log_level: str | None = None,
    sample_ratio: float | None = None,
    *,
    force: bool = False,
):
    """Context manager to automatically init and teardown observability."""
    init_observability(
        app_name=app_name,
        environment=environment,
        namespace=namespace,
        log_level=log_level,
        sample_ratio=sample_ratio,
        force=force,
    )
    try:
        yield
    finally:
        shutdown_observability()
