from __future__ import annotations

import logging
import sys

from contextlib import suppress

_DIAGNOSTIC_LOGGER = None


def get_diagnostic_logger() -> logging.Logger:
    """Singleton C0 diagnostic logger — no formatter, no pipeline, no handlers from C1."""
    global _DIAGNOSTIC_LOGGER
    if _DIAGNOSTIC_LOGGER is not None:
        return _DIAGNOSTIC_LOGGER

    logger = logging.getLogger("quantum.internal.diagnostics")
    logger.setLevel(logging.ERROR)
    logger.propagate = False

    try:
        handler = logging.StreamHandler(sys.stderr)
    except Exception:
        # If stderr fails (extremely rare), fallback to /dev/null
        with suppress(Exception):
            handler = logging.FileHandler("/dev/null")

    formatter = logging.Formatter(
        fmt="[INTERNAL][%(levelname)s] %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    _DIAGNOSTIC_LOGGER = logger
    return logger
