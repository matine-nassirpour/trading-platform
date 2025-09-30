import logging
import os
import threading
from typing import Literal

from prometheus_client import start_http_server

from quantum.adapters.telemetry.context.run_id import generate_run_id
from quantum.adapters.telemetry.logging.logs import LoggingConfig, init_logging
from quantum.adapters.telemetry.tracing.propagation import setup_propagation
from quantum.adapters.telemetry.tracing.traces import TracingConfig, init_tracing
from quantum.foundation.config.env import load_local_env

_initialized = False
_init_lock = threading.Lock()


def init_observability(
    app_name: str = "python_core",
    environment: str = "dev",
    namespace: str = "quantum",
    log_level: str = "INFO",
    sample_ratio: float = 1.0,
) -> None:
    """Idempotent + thread-safe observability bootstrap."""
    global _initialized
    if _initialized:
        return

    with _init_lock:
        if _initialized:
            return

        load_local_env()
        generate_run_id()

        # Read config from environment (OS > .env)
        app_name = os.getenv("QUANTUM_APP_NAME", app_name)
        environment = os.getenv("QUANTUM_ENV", environment)
        namespace = os.getenv("QUANTUM_NS", namespace)
        log_level = os.getenv("QUANTUM_LOG_LEVEL", log_level)
        sample_ratio = float(os.getenv("QUANTUM_TRACE_SAMPLE", sample_ratio))

        # Logging JSON
        init_logging(
            LoggingConfig(
                app_name=app_name,
                environment=environment,
                namespace=namespace,
                log_level=log_level,
            )
        )

        exp_env = os.getenv("QUANTUM_TRACE_EXPORTER")
        exporter: Literal["console", "none"] = (
            "none" if exp_env == "none" else "console"
        )

        # Tracing OTel
        init_tracing(
            TracingConfig(
                service_name=app_name,
                environment=environment,
                namespace=namespace,
                exporter=exporter,
                sample_ratio=sample_ratio,
            )
        )
        setup_propagation()

        # Prometheus metrics endpoint (opt-in)
        port = int(os.getenv("QUANTUM_METRICS_PORT", "0") or "0")
        addr = os.getenv("QUANTUM_METRICS_ADDR", "127.0.0.1")
        if port > 0:
            try:
                start_http_server(port, addr=addr)
            except OSError as e:
                logging.getLogger(__name__).warning(
                    f"Metrics HTTP server failed to start on {addr}:{port}: {e}"
                )

        _initialized = True
