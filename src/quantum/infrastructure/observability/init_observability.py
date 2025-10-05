import logging
import os
import threading
from contextlib import contextmanager, suppress
from pathlib import Path
from typing import Literal

from prometheus_client import start_http_server

from quantum.infrastructure.observability.logging.logs import (
    LoggingConfig,
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
from quantum.infrastructure.observability.tracing.propagation import setup_propagation
from quantum.infrastructure.observability.tracing.traces import (
    TracingConfig,
    init_tracing,
)
from quantum.shared.config.env_loader import load_env
from quantum.shared.context.run_id import generate_run_id, get_run_id

_initialized = False
_init_lock = threading.Lock()
_metrics_httpd_started = False
_tracer_provider_ref: object | None = None


def _probe_logging_sinks() -> bool:
    """
    Lightweight heuristics to verify that persistent handlers are operational.
    We avoid writing anything: we simply check the accessibility of the folders.
    """
    ok = True
    root = logging.getLogger()
    for h in root.handlers:
        base_dir = getattr(h, "base_dir", None)
        if base_dir is not None:
            try:
                os.makedirs(base_dir, exist_ok=True)
                if not os.access(base_dir, os.W_OK):
                    ok = False
                if os.getenv("QUANTUM_LOG_DEEP_PROBE", "0") == "1":
                    test_dir = Path(base_dir) / "__probe__/yyyy/mm/dd/hh"
                    test_dir.mkdir(parents=True, exist_ok=True)
                    test_file = test_dir / "probe.jsonl"
                    with open(test_file, "a", encoding="utf-8") as f:
                        f.write("{}\n")
                    test_file.unlink(missing_ok=True)
                    try:
                        test_dir.rmdir()
                    except OSError:
                        pass
            except OSError:
                ok = False
    return ok


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
        sample_ratio = (
            0.0 if sample_ratio < 0.0 else (1.0 if sample_ratio > 1.0 else sample_ratio)
        )

        # Logging JSON
        logging_ok = False
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
            if _probe_logging_sinks():
                logging_sink_up.set(1)
                logging_ok = True
            else:
                logging.getLogger(__name__).warning("Logging sinks not writable")
        except Exception as e:
            logging.getLogger(__name__).exception(f"Logging initialization failed: {e}")

        exp_env = os.getenv("QUANTUM_TRACE_EXPORTER", "").strip().lower()
        # supports: otlp | console | none (default: console)
        exporter: Literal["otlp", "console", "none"]
        if exp_env in {"otlp", "console", "none"}:
            exporter = exp_env  # type: ignore[assignment]
        else:
            exporter = "console"  # safe default

        pipeline_logging_ok.set(1 if logging_ok else 0)

        # Tracing OTel
        tracing_ok = False
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

        ok = logging_ok and tracing_ok
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
            _shutdown_tracing_if_any()
        finally:
            if set_gauges_down:
                # Gauge may fail if client/registry isn't initialized
                with suppress(ValueError, RuntimeError):
                    otel_tracing_up.set(0)

    # Logging
    if close_logging:
        try:
            root = logging.getLogger()
            # Copy to iterate safely
            for h in list(root.handlers):
                # flush before close if possible
                flush = getattr(h, "flush", None)
                if callable(flush):
                    with suppress(OSError, ValueError, RuntimeError, TypeError):
                        flush()

                # close handler (bad FD/state may raise)
                with suppress(OSError, ValueError, RuntimeError, TypeError):
                    h.close()

                # removeHandler raises ValueError if not attached
                with suppress(ValueError):
                    root.removeHandler(h)
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
