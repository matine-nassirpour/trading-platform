import os

from quantum.infrastructure.observability.init_observability import init_observability


def init_streamlit() -> None:
    os.environ.setdefault("QUANTUM_METRICS_PORT", "0")
    try:
        sample_ratio = float(os.getenv("QUANTUM_TRACE_SAMPLE", "1.0"))
    except (TypeError, ValueError):
        sample_ratio = 1.0

    init_observability(
        app_name="streamlit_ui",
        environment=os.getenv("QUANTUM_ENV", "dev"),
        namespace=os.getenv("QUANTUM_NS", "quantum"),
        log_level=os.getenv("QUANTUM_LOG_LEVEL", "INFO"),
        sample_ratio=sample_ratio,
    )
