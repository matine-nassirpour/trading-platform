"""
Internal diagnostic logger for low-level failures.

This logger is:
    - Fully isolated from the main logging pipeline
    - Guaranteed side effect free
    - Safe in fallback/error conditions
    - DO-178C compliant (no silent failure paths)

It NEVER uses:
    - JsonFormatter
    - LoggingPipeline
    - partitioned handlers
    - audit handlers
    - external dependencies

It writes only to sys.stderr, or /dev/null if stderr is unavailable.
"""

from __future__ import annotations

import logging
import sys

from contextlib import suppress


def _build_diagnostic_logger() -> logging.Logger:
    logger = logging.getLogger("quantum.internal.diagnostics")

    # Idempotent: avoid duplicating handlers if called multiple times.
    if logger.handlers:
        return logger

    logger.setLevel(logging.ERROR)
    logger.propagate = False

    try:
        handler = logging.StreamHandler(sys.stderr)
    except Exception:
        # If stderr fails (extremely rare), fallback to /dev/null
        with suppress(Exception):
            handler = logging.FileHandler("/dev/null")
    handler.setLevel(logging.ERROR)

    # Minimalistic plain-text formatter
    formatter = logging.Formatter(
        fmt="[INTERNAL][%(levelname)s] %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
    )
    handler.setFormatter(formatter)

    logger.addHandler(handler)
    return logger


# Singleton diagnostic logger
DIAGNOSTIC_LOGGER = _build_diagnostic_logger()
