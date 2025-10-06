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
from quantum.shared.config.env_flags import get_bool
from quantum.shared.config.env_loader import load_env
from quantum.shared.context.run_id import generate_run_id, get_run_id

_initialized = False
_init_lock = threading.Lock()
_metrics_httpd_started = False
_tracer_provider_ref: object | None = None


def _iter_persistent_handlers() -> list[logging.Handler]:
    """
    Returns the list of handlers considered "persistent" (write to disk), i.e., handlers that expose a `base_dir` attribute, by aggregating:

    - root.handlers (partitioned JSONL if enabled)
    - logger 'quantum.trading' (audit handler if enabled)
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
            test_dir = base / "__probe__/yyyy/mm/dd/hh"
            test_dir.mkdir(parents=True, exist_ok=True)
            test_file = test_dir / "probe.jsonl"
            with open(test_file, "a", encoding="utf-8") as f:
                f.write("{}\n")
            test_file.unlink(missing_ok=True)
            with suppress(OSError):
                test_dir.rmdir()
        return True
    except OSError:
        return False


def _probe_logging_sinks() -> bool:
    """
    Semantics A: Returns True if **at least one** persistent sink (partition or audit)
    is present **and** writable. If no persistent sink is attached, returns False.
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
    """
    Best effort shutdown of previous tracer provider (if any)
    to allow a clean re-init when force=True or after partial failures.
    """
    global _tracer_provider_ref
    tp = _tracer_provider_ref
    if tp is None:
        return

    shutdown = getattr(tp, "shutdown", None)
    if callable(shutdown):
        try:
            shutdown()
        except (RuntimeError, OSError, TimeoutError) as e:
            logging.getLogger(__name__).debug(f"Tracer shutdown failed: {e}")

    _tracer_provider_ref = None


def init_observability(
    app_name: str = "python_core",
    environment: str = "dev",
    namespace: str = "quantum",
    log_level: str = "INFO",
    sample_ratio: float = 1.0,
    *,
    force: bool = False,
) -> None:
    """Idempotent + thread-safe observability bootstrap."""
    global _initialized, _metrics_httpd_started

    if _initialized and not force:
        return

    with _init_lock:
        if _initialized and not force:
            return

        # Reset health
        pipeline_up.set(0)
        otel_tracing_up.set(0)
        logging_sink_up.set(0)

        # Reset pillars
        pipeline_logging_ok.set(0)
        pipeline_tracing_ok.set(0)
        pipeline_metrics_http_ok.set(0)

        load_env()  # does not overwrite existing env by default
        with suppress(ValueError, RuntimeError, AttributeError, NameError):
            refresh_build_info_from_env()

        if not get_run_id():
            generate_run_id()

        # Read config from environment (OS > .env)
        app_name = os.getenv("QUANTUM_APP_NAME", app_name)
        environment = os.getenv("QUANTUM_ENV", environment)
        namespace = os.getenv("QUANTUM_NS", namespace)
        log_level = os.getenv("QUANTUM_LOG_LEVEL", log_level)
        app_version = os.getenv("QUANTUM_APP_VERSION", "0.0.0")
        try:
            sample_ratio = float(os.getenv("QUANTUM_TRACE_SAMPLE", sample_ratio))
        except (TypeError, ValueError):
            sample_ratio = 1.0
        sample_ratio = max(0.0, min(1.0, sample_ratio))

        if force:
            close_and_remove_all_handlers(logging.getLogger())

        # JSON logging (initialization)
        logging_initialized = False
        try:
            init_logging(
                LoggingConfig(
                    app_name=app_name,
                    environment=environment,
                    namespace=namespace,
                    log_level=log_level,
                    app_version=app_version,
                )
            )
            logging_initialized = True
        except Exception as e:
            logging.getLogger(__name__).exception(f"Logging initialization failed: {e}")

        pipeline_logging_ok.set(1 if logging_initialized else 0)

        # Persistent sinks up? (partition and/or audit)
        try:
            sinks_ok = _probe_logging_sinks()
        except Exception as e:
            logging.getLogger(__name__).warning(f"Logging sinks probe failed: {e}")
            sinks_ok = False

        logging_sink_up.set(1 if sinks_ok else 0)

        # Tracing OTel
        tracing_ok = False
        exp_env = os.getenv("QUANTUM_TRACE_EXPORTER", "").strip().lower()
        exporter: Literal["otlp", "console", "none"] = (
            exp_env if exp_env in {"otlp", "console", "none"} else "console"
        )
        try:
            _shutdown_tracing_if_any()
            tp = init_tracing(
                TracingConfig(
                    service_name=app_name,
                    environment=environment,
                    namespace=namespace,
                    exporter=exporter,
                    sample_ratio=sample_ratio,
                ),
                replace_existing=force,
            )
            setup_propagation()
            # Do not re-attach if already present.
            install_process_baggage()
            otel_tracing_up.set(1)
            tracing_ok = bool(tp)
            global _tracer_provider_ref
            _tracer_provider_ref = tp
        except Exception as e:
            logging.getLogger(__name__).exception(f"Tracing initialization failed: {e}")
            otel_tracing_up.set(0)
            # Fallback (retry 1 time): export 'none' + sample 0.0
            try:
                tp = init_tracing(
                    TracingConfig(
                        service_name=app_name,
                        environment=environment,
                        namespace=namespace,
                        exporter="none",
                        sample_ratio=0.0,
                    )
                )
                setup_propagation()
                install_process_baggage()
                otel_tracing_up.set(1)
                tracing_ok = True
                _tracer_provider_ref = tp
                logging.getLogger(__name__).warning(
                    "Tracing fallback activated: exporter=none, sample_ratio=0.0"
                )
            except Exception as e2:
                logging.getLogger(__name__).exception(f"Tracing fallback failed: {e2}")
                otel_tracing_up.set(0)

        pipeline_tracing_ok.set(1 if tracing_ok else 0)

        # Prometheus metrics endpoint (opt-in, start-once)
        port = int(os.getenv("QUANTUM_METRICS_PORT", "0") or "0")
        addr = os.getenv("QUANTUM_METRICS_ADDR", "127.0.0.1")
        if port > 0 and not _metrics_httpd_started:
            try:
                start_http_server(port, addr=addr)
                _metrics_httpd_started = True
                pipeline_metrics_http_ok.set(1)
            except OSError as e:
                logging.getLogger(__name__).warning(
                    f"Metrics HTTP server failed to start on {addr}:{port}: {e}"
                )
                pipeline_metrics_http_ok.set(0)
        else:
            # No HTTP exposure requested → stay at 0 (this is intentional and non-blocking)
            pipeline_metrics_http_ok.set(1 if _metrics_httpd_started else 0)

        ok = logging_initialized and tracing_ok
        pipeline_up.set(1 if ok else 0)
        _initialized = bool(ok)


def shutdown_observability(
    *,
    close_logging: bool = True,
    shutdown_tracing: bool = True,
    reset_state: bool = True,
    set_gauges_down: bool = False,
) -> None:
    """
    Clean and idempotent shutdown of observability components.

    - Closes/flushes logging handlers and removes the root logger.
    - Stops the OTel provider tracer if present.
    - Optional: Resets the gauges to 0 (useful for testing). In normal run, leave this as False.
    - Optional: Resets internal flags to allow a clean reset afterward.
    """
    global _initialized, _tracer_provider_ref

    # Tracing
    if shutdown_tracing:
        try:
            detach_process_baggage_if_any()
        finally:
            _shutdown_tracing_if_any()
            if set_gauges_down:
                # Gauge may fail if client/registry isn't initialized
                with suppress(ValueError, RuntimeError):
                    otel_tracing_up.set(0)

    # Logging
    if close_logging:
        try:
            close_and_remove_all_handlers(logging.getLogger())
        finally:
            if set_gauges_down:
                with suppress(NameError, AttributeError, ValueError, RuntimeError):
                    logging_sink_up.set(0)

    # Global pipeline (optional)
    if set_gauges_down:
        with suppress(NameError, AttributeError, ValueError, RuntimeError):
            pipeline_up.set(0)

    if reset_state:
        _initialized = False
        # Do not set _metrics_httpd_started to False: we do not "unmount" the prometheus_client HTTPD
        # (start_http_server does not provide a stop; it is a process server).


@contextmanager
def observability_session(
    app_name: str = "python_core",
    environment: str = "dev",
    namespace: str = "quantum",
    log_level: str = "INFO",
    sample_ratio: float = 1.0,
    *,
    force: bool = False,
):
    """
    Practical context for tests/e2e:
    init_observability(...) then shutdown_observability() on exit.
    """
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
