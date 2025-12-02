"""
Defines the canonical mapping between Python logging levels
and OpenTelemetry-compatible severity names and numbers.

This mapping is used across all observability components to
ensure consistent interpretation of log severity.
"""

from __future__ import annotations

import logging

from collections.abc import Mapping
from types import MappingProxyType
from typing import Final, Literal

from quantum.infrastructure.observability.foundation.metrics.c0_metric_registry import (
    define_counter,
)

SeverityText = Literal["TRACE", "DEBUG", "INFO", "WARN", "ERROR", "FATAL"]
SeverityPair = tuple[SeverityText, int]
SeverityMapType = Mapping[int, SeverityPair]
ReverseTextMapType = Mapping[str, int]
ReverseLevelMapType = Mapping[str, int]

_CANONICAL_SEVERITY_MAP: Final[SeverityMapType] = MappingProxyType(
    {
        logging.NOTSET: ("TRACE", 1),
        logging.DEBUG: ("DEBUG", 5),
        logging.INFO: ("INFO", 9),
        logging.WARNING: ("WARN", 13),
        logging.ERROR: ("ERROR", 17),
        logging.CRITICAL: ("FATAL", 21),
    }
)

_REV_TEXT_TO_NUMBER: Final[ReverseTextMapType] = MappingProxyType(
    {text: number for (text, number) in _CANONICAL_SEVERITY_MAP.values()}
)

_REV_TEXT_TO_LEVELNO: Final[ReverseLevelMapType] = MappingProxyType(
    {text: levelno for (levelno, (text, _)) in _CANONICAL_SEVERITY_MAP.items()}
)

_SEVERITY_MAPPING_ERRORS = define_counter("severity_mapping_errors")


# ╭────────────────────────────────────────────────────────────────────────────╮
# │ Public API                                                                 │
# ╰────────────────────────────────────────────────────────────────────────────╯
def canonical_severity(levelno: int) -> SeverityPair:
    """
    Return the canonical (severity_text, severity_number) pair for a Python
    logging level.
    """
    try:
        return _CANONICAL_SEVERITY_MAP[levelno]
    except Exception:
        _SEVERITY_MAPPING_ERRORS.inc()
        return "ERROR", 17


def severity_number_from_text(text: str) -> int:
    """
    Return the canonical numeric severity for a severity text.
    """
    if not isinstance(text, str):
        raise ValueError(f"severity text must be string, got {type(text).__name__}")

    key = text.upper()
    try:
        return _REV_TEXT_TO_NUMBER[key]
    except KeyError:
        raise ValueError(f"Unknown severity text: {text!r}") from None


# ╭────────────────────────────────────────────────────────────────────────────╮
# │ Expose read-only mappings for external safe inspection                     │
# ╰────────────────────────────────────────────────────────────────────────────╯
SEVERITY_MAP: Final[SeverityMapType] = _CANONICAL_SEVERITY_MAP
SEVERITY_TEXT_TO_NUMBER: Final[ReverseTextMapType] = _REV_TEXT_TO_NUMBER
SEVERITY_TEXT_TO_LEVELNO: Final[ReverseLevelMapType] = _REV_TEXT_TO_LEVELNO
