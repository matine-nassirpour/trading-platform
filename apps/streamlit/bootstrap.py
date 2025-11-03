import logging
import threading

from quantum.infrastructure.observability.bootstrap.init_manager import (
    init_observability,
)
from quantum.infrastructure.observability.context.run_id import (
    generate_run_id,
    get_run_id,
)

# ╭────────────────────────────────────────────────────────────────────────────╮
# │ Global guards                                                              │
# ╰────────────────────────────────────────────────────────────────────────────╯

_BOOTSTRAP_LOCK = threading.Lock()
_BOOTSTRAP_DONE = False


# ╭────────────────────────────────────────────────────────────────────────────╮
# │ Public API                                                                 │
# ╰────────────────────────────────────────────────────────────────────────────╯
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


# ╭────────────────────────────────────────────────────────────────────────────╮
# │ Internal logic                                                             │
# ╰────────────────────────────────────────────────────────────────────────────╯
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

    logger.info("Quantum Streamlit bootstrap completed successfully.")
