import logging
import threading

# from quantum.infrastructure.execution.gateway_registry import get_gateway
# from quantum.infrastructure.execution.mt5_gateway import (
#     init_mt5_terminal,
#     shutdown_mt5_terminal,
# )
from quantum.infrastructure.observability.bootstrap.init_manager import (
    init_observability,
)
from quantum.infrastructure.observability.context.run_id import (
    generate_run_id,
    get_run_id,
)

# ╭─────────────────────────────────────────────────────────────────────────────╮
# │ Global guards                                                               │
# ╰─────────────────────────────────────────────────────────────────────────────╯

_BOOTSTRAP_LOCK = threading.Lock()
_BOOTSTRAP_DONE = False


# ╭─────────────────────────────────────────────────────────────────────────────╮
# │ Public API                                                                  │
# ╰─────────────────────────────────────────────────────────────────────────────╯


def init_streamlit() -> None:
    """
    Thread-safe and idempotent initialization for the Streamlit Quantum environment.

    Ensures:
    - Observability stack (logging, tracing, metrics) is initialized once.
    - MT5 terminals are bootstrapped for all configured execution channels.
    - Safe re-entry on Streamlit "rerun" or multithreaded reload.
    """
    global _BOOTSTRAP_DONE

    if _BOOTSTRAP_DONE:
        return  # Fast path: already initialized

    with _BOOTSTRAP_LOCK:
        # Double-checked locking
        if _BOOTSTRAP_DONE:
            return

        try:
            _perform_streamlit_init()
            _BOOTSTRAP_DONE = True
        except Exception as e:
            # Ensure consistent recovery state (no partial init)
            logger = logging.getLogger("apps.streamlit.bootstrap")
            logger.exception(f"Streamlit bootstrap failed: {e}")
            raise


# ╭─────────────────────────────────────────────────────────────────────────────╮
# │ Internal logic                                                              │
# ╰─────────────────────────────────────────────────────────────────────────────╯


def _perform_streamlit_init() -> None:
    """
    Encapsulates the actual initialization logic (observability + MT5 terminals).
    This function is invoked once under a thread-safe lock.
    """

    if not get_run_id():
        generate_run_id()

    init_observability()

    logger = logging.getLogger("apps.streamlit.bootstrap")
    logger.info("Initializing Quantum Streamlit UI with observability stack...")

    # _bootstrap_mt5_terminals(logger)
    # _validate_mt5_credentials(logger)

    logger.info("Quantum Streamlit bootstrap completed successfully.")


# def _bootstrap_mt5_terminals(logger: logging.Logger) -> None:
#     """
#     Bootstraps all configured MetaTrader5 terminals (FTMO, FundedNext, etc.).
#     Ensures each terminal path is reachable and initialized once.
#     """
#     tracer = get_tracer("apps.streamlit.bootstrap")
#
#     with tracer.start_as_current_span("ui.mt5_bootstrap"):
#         for channel in ExecutionChannel:
#             gw = get_gateway(channel)
#             term_path = gw.get("terminal_path")
#
#             if not term_path or not os.path.exists(term_path):
#                 logger.warning(f"Terminal path not found for {channel}: {term_path}")
#                 continue
#
#             try:
#                 ok = init_mt5_terminal(channel, term_path)
#                 if ok:
#                     logger.info(f"MT5 terminal initialized for {channel}")
#                 else:
#                     logger.error(f"Failed to initialize MT5 terminal for {channel}")
#             except Exception as e:
#                 logger.exception(
#                     f"Exception initializing MT5 terminal for {channel}: {e}"
#                 )
#
#     # Register graceful shutdown only once
#     atexit.register(_safe_shutdown, logger)
#
#
# def _validate_mt5_credentials(logger: logging.Logger) -> None:
#     """
#     Validates that all MT5 credentials (login/server/password) are defined.
#     Raises a RuntimeError immediately if a configuration is missing.
#     """
#     for channel in (ExecutionChannel.FTMO, ExecutionChannel.FUNDEDNEXT):
#         creds = ConfigManager.get_mt5_credentials(channel.name)
#         if not all(creds.values()):
#             raise RuntimeError(
#                 f"Missing credentials for {channel.name} in .env — "
#                 f"please define MT5_{channel.name.upper()}_LOGIN, "
#                 f"MT5_{channel.name.upper()}_SERVER and "
#                 f"MT5_{channel.name.upper()}_PASSWORD."
#             )
#
#     logger.info("MT5 credentials successfully validated for all channels.")


# def _safe_shutdown(logger: logging.Logger) -> None:
#     """Gracefully shuts down all MetaTrader5 terminals on process exit."""
#     try:
#         shutdown_mt5_terminal()
#         logger.info("MT5 terminals shutdown completed.")
#     except Exception as e:
#         logger.exception(f"MT5 terminal shutdown error: {e}")
