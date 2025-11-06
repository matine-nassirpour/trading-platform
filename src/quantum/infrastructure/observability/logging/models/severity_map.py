"""
Defines the canonical mapping between Python logging levels
and OpenTelemetry-compatible severity names and numbers.

This mapping is used across all observability components to
ensure consistent interpretation of log severity.
"""

from __future__ import annotations

import logging

from typing import Final

from quantum.infrastructure.observability.logging.models.log_payload_v1 import (
    SeverityText,
)

SeverityMapType = dict[int, tuple[SeverityText, int]]

SEVERITY_MAP: Final[SeverityMapType] = {
    logging.NOTSET: ("TRACE", 1),
    logging.DEBUG: ("DEBUG", 5),
    logging.INFO: ("INFO", 9),
    logging.WARNING: ("WARN", 13),
    logging.ERROR: ("ERROR", 17),
    logging.CRITICAL: ("FATAL", 21),
}
