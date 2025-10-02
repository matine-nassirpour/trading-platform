from quantum.infrastructure.observability.init_observability import init_observability


def init_cli() -> None:
    init_observability(
        app_name="python_core",
        environment="dev",
        namespace="quantum",
        log_level="INFO",
        sample_ratio=1.0,
    )
