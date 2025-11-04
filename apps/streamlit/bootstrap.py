from __future__ import annotations

import logging
import threading

from runtime.runtime_composer import get_runtime

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
    - A unique run_id is generated for each runtime.
    - Safe re-entry across Streamlit reruns and multithreaded reloads.
    """
    global _BOOTSTRAP_DONE

    if _BOOTSTRAP_DONE:
        return  # Already initialized

    with _BOOTSTRAP_LOCK:
        if _BOOTSTRAP_DONE:
            return

        try:
            _perform_streamlit_init()
            _BOOTSTRAP_DONE = True
        except Exception as e:
            logger = logging.getLogger("apps.streamlit.bootstrap")
            logger.exception("Streamlit bootstrap failed: %s", e)
            raise


# ╭────────────────────────────────────────────────────────────────────────────╮
# │ Internal logic                                                             │
# ╰────────────────────────────────────────────────────────────────────────────╯
def _perform_streamlit_init() -> None:
    """
    Encapsulates the actual initialization logic (observability, run_id, etc.).
    """
    runtime = get_runtime()

    obs = runtime.observability_provider
    obs.ensure_run_id()
    obs.initialize_observability()

    logger = logging.getLogger("apps.streamlit.bootstrap")
    logger.info("Initializing Quantum Streamlit UI with observability stack...")
    logger.info("Quantum Streamlit bootstrap completed successfully.")
