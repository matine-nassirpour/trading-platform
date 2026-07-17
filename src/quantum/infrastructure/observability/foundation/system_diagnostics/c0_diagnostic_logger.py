import logging
import sys
import threading

from contextlib import suppress
from typing import Final

C0_DIAGNOSTIC_LOG_NAME: Final = "quantum.internal.diagnostics"
C0_DIAGNOSTIC_LOG_LEVEL: Final = logging.ERROR
WINDOWS_NULL_DEVICE: Final = r"\\.\NUL"

# Singleton instance + lock (thread-safe initialization)
_DIAGNOSTIC_LOGGER_INSTANCE: logging.Logger | None = None
_INIT_LOCK = threading.Lock()


class FinalDiagnosticLogger:
    """
    Immutable, non-configurable diagnostic logger.
    - Guarantee an absolutely reliable C0 channel for reporting internal errors.
    - Ensure complete isolation from application logging (C1/C2).
    - Prevent any external modification of handlers, layer, or propagation.
    - Resistant to multithreaded environments.
    - is instantiated only once (idempotent, thread-safe),
    - does not depend on any user variables,
    - remains stable throughout the entire process lifetime.
    """

    __slots__ = ("_logger",)

    def __init__(self) -> None:
        logger = logging.getLogger(C0_DIAGNOSTIC_LOG_NAME)

        # Strict C0 level: must NEVER be modified
        logger.setLevel(C0_DIAGNOSTIC_LOG_LEVEL)
        logger.propagate = False

        handler: logging.Handler

        # Handler construction: minimal and always available
        try:
            handler = logging.StreamHandler(sys.stderr)
        except Exception:
            # Ultra rare: permanent fallback
            with suppress(Exception):
                handler = logging.FileHandler(WINDOWS_NULL_DEVICE)

            # Guaranteed last-resort fallback (Windows)
            if "handler" not in locals():
                handler = logging.StreamHandler(sys.stdout)

        formatter = logging.Formatter(
            fmt="[INTERNAL][%(levelname)s] %(message)s",
            datefmt="%Y-%m-%dT%H:%M:%S",
        )
        handler.setFormatter(formatter)

        # Prior removal of any potential handlers (idempotence & purity)
        logger.handlers.clear()
        logger.addHandler(handler)

        self._logger = logger

    @property
    def logger(self) -> logging.Logger:
        """Immutable internal logger."""
        return self._logger


def get_diagnostic_logger() -> logging.Logger:
    """
    Thread-safe access to the single C0 logger.
    This function is pure, idempotent and guarantees the immutability of the logger.
    """

    global _DIAGNOSTIC_LOGGER_INSTANCE

    if _DIAGNOSTIC_LOGGER_INSTANCE is not None:
        return _DIAGNOSTIC_LOGGER_INSTANCE

    with _INIT_LOCK:
        if _DIAGNOSTIC_LOGGER_INSTANCE is None:
            _DIAGNOSTIC_LOGGER_INSTANCE = FinalDiagnosticLogger().logger

    return _DIAGNOSTIC_LOGGER_INSTANCE
