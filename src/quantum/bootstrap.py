from quantum.adapters.telemetry.logging.logs import LoggingConfig, init_logging
from quantum.adapters.telemetry.tracing.propagation import setup_propagation
from quantum.adapters.telemetry.tracing.traces import TracingConfig, init_tracing

_initialized = False


def init_observability(
    app_name: str = "python_core",
    environment: str = "dev",
    namespace: str = "quantum",
    log_level: str = "INFO",
    sample_ratio: float = 1.0,
) -> None:
    global _initialized
    if _initialized:
        return

    init_logging(
        LoggingConfig(
            app_name=app_name,
            environment=environment,
            namespace=namespace,
            log_level=log_level,
        )
    )

    init_tracing(
        TracingConfig(
            service_name=app_name,
            environment=environment,
            namespace=namespace,
            exporter="console",
            sample_ratio=sample_ratio,
        )
    )

    setup_propagation()

    _initialized = True
