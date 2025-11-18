from __future__ import annotations

import logging
import sys

from contextlib import suppress
from typing import Final

LOGGER: Final = logging.getLogger("quantum.internal.diagnostics")
_DIAGNOSTIC_LOGGER = None


def get_diagnostic_logger() -> logging.Logger:
    """Singleton C0 diagnostic logger — no formatter, no pipeline, no handlers from C1."""
    global _DIAGNOSTIC_LOGGER
    if _DIAGNOSTIC_LOGGER is not None:
        return _DIAGNOSTIC_LOGGER

    LOGGER.setLevel(logging.ERROR)
    LOGGER.propagate = False

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
    LOGGER.addHandler(handler)

    _DIAGNOSTIC_LOGGER = LOGGER
    return LOGGER
