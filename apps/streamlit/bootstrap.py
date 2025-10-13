import atexit
import logging
import os

from quantum.infrastructure.execution.gateway_registry import get_gateway
from quantum.infrastructure.execution.mt5_gateway import (
    init_mt5_terminal,
    shutdown_mt5_terminal,
)
from quantum.infrastructure.observability.init_observability import init_observability
from quantum.infrastructure.observability.tracing.traces import get_tracer
from quantum.shared.config.env_loader import get_mt5_credentials
from quantum.shared.context.run_id import generate_run_id, get_run_id
from quantum.shared.types.channels import ExecutionChannel

# Global guard to avoid duplicate initialization (Streamlit reruns)
_ALREADY_BOOTSTRAPPED = False


def init_streamlit() -> None:
    """
    Initializes the Streamlit Quantum application environment.

    Responsibilities:
    -----------------
    - Ensures all observability subsystems (logging, tracing, metrics) are initialized.
    - Guarantees a stable `run_id` is available for correlation across components.
    - Initializes local MetaTrader5 terminals for each configured execution channel.
    - Ensures graceful shutdown of terminals when the Streamlit app exits.

    Notes:
    ------
    - The logging system is initialized implicitly by `init_observability()`.
    - All logs use the Quantum structured pipeline (context-aware, OTEL-compatible).
    - MT5 terminals are bootstrapped only if their executable paths exist locally.
    """

    global _ALREADY_BOOTSTRAPPED
    if _ALREADY_BOOTSTRAPPED:
        return

    os.environ.setdefault("QUANTUM_METRICS_PORT", "0")

    # Tracing sample ratio
    try:
        sample_ratio = float(os.getenv("QUANTUM_TRACE_SAMPLE", "1.0"))
    except (TypeError, ValueError):
        sample_ratio = 1.0

    if not get_run_id():
        generate_run_id()

    init_observability(
        app_name="streamlit_ui",
        environment=os.getenv("QUANTUM_ENV", "dev"),
        namespace=os.getenv("QUANTUM_NS", "quantum"),
        log_level=os.getenv("QUANTUM_LOG_LEVEL", "INFO"),
        sample_ratio=sample_ratio,
    )

    logger = logging.getLogger("apps.streamlit.bootstrap")
    logger.info("🚀 Initializing Quantum Streamlit UI with observability stack...")

    _bootstrap_terminals(logger)
    _ALREADY_BOOTSTRAPPED = True

    for channel in (ExecutionChannel.FTMO, ExecutionChannel.FUNDEDNEXT):
        creds = get_mt5_credentials(channel.name)
        if not all(creds.values()):
            raise RuntimeError(
                f"❌ Missing credentials for {channel.name} in .env — "
                f"please define MT5_{channel.name.upper()}_LOGIN, "
                f"MT5_{channel.name.upper()}_SERVER and "
                f"MT5_{channel.name.upper()}_PASSWORD."
            )

    logger.info("🔐 MT5 credentials successfully validated for all channels.")


def _bootstrap_terminals(logger: logging.Logger) -> None:
    """
    Attempts to initialize all configured MT5 terminals.

    This ensures each execution channel (e.g., FTMO, FundedNext) is ready
    for interaction before the UI starts dispatching commands.
    """

    tracer = get_tracer("apps.streamlit.bootstrap")

    with tracer.start_as_current_span("ui.mt5_bootstrap"):
        for channel in ExecutionChannel:
            gw = get_gateway(channel)
            term_path = gw.get("terminal_path")

            if not term_path or not os.path.exists(term_path):
                logger.warning(f"⚠️ Terminal path not found for {channel}: {term_path}")
                continue

            try:
                ok = init_mt5_terminal(channel, term_path)
                if ok:
                    logger.info(f"✅ MT5 terminal initialized for {channel}")
                else:
                    logger.error(f"❌ Failed to initialize MT5 terminal for {channel}")
            except Exception as e:
                logger.exception(
                    f"💥 Exception initializing MT5 terminal for {channel}: {e}"
                )

    # Register a shutdown hook once
    atexit.register(_shutdown_all_terminals, logger)


def _shutdown_all_terminals(logger: logging.Logger) -> None:
    """Ensures all terminals are properly shut down on application exit."""
    try:
        shutdown_mt5_terminal()
        logger.info("🧹 MT5 terminals shutdown completed.")
    except Exception as e:
        logger.exception(f"MT5 terminal shutdown error: {e}")
