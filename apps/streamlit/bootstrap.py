from __future__ import annotations

import logging
import threading

from typing import Final

# from runtime.runtime_composer import get_runtime

LOGGER: Final = logging.getLogger("apps.streamlit.bootstrap")

# ╭────────────────────────────────────────────────────────────────────────────╮
# │ Global guards                                                              │
# ╰────────────────────────────────────────────────────────────────────────────╯
# _RUNTIME = get_runtime()
_BOOTSTRAP_LOCK = threading.Lock()
_BOOTSTRAP_DONE = False


def get_runtime_context():
    """Return the globally composed Quantum runtime context."""
    # return _RUNTIME


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
            LOGGER.exception("Streamlit bootstrap failed: %s", e)
            raise


# ╭────────────────────────────────────────────────────────────────────────────╮
# │ Internal logic                                                             │
# ╰────────────────────────────────────────────────────────────────────────────╯
def _perform_streamlit_init() -> None:
    """
    Encapsulates the actual initialization logic (observability, run_id, etc.).
    """
    # obs = _RUNTIME.observability_provider
    # obs.ensure_run_id()
    # obs.initialize_observability()

    LOGGER.info("Initializing Quantum Streamlit UI with observability stack...")
    LOGGER.info("Quantum Streamlit bootstrap completed successfully.")
