from __future__ import annotations

import traceback

from logging import LogRecord
from typing import Any, Final

from quantum.infrastructure.observability.logging.runtime.metrics import define_counter

_EXCEPTION_EXTRACTION_FAILURES: Final = define_counter(
    "logging_exception_extraction_failures"
)


class ExceptionProcessor:
    """
    Unified, deterministic and schema-safe exception block builder.

    This processor centralizes all exception extraction logic used by
    the structured logging system. It is the single source of truth for
    generating exception blocks consumed by LogPayload and fallback
    JSON payloads.

    Guarantees:
    - Stable field names
    - Deterministic output for a given exc_info
    - Safe against recursive exceptions
    - No traceback formatting failures bubbling up
    - No duplication between `exception` and `exception_stacktrace`
    """

    __slots__ = ()

    # --------------------------------------------------------------------------
    # Internal Helpers
    # --------------------------------------------------------------------------
    @staticmethod
    def _extract_basic_info(exc_info: Any) -> tuple[str | None, str | None]:
        etype, evalue, _ = exc_info
        exc_type = getattr(etype, "__name__", str(etype)) if etype else None

        try:
            exc_message = str(evalue) if evalue is not None else None
        except Exception:
            exc_message = None

        return exc_type, exc_message

    @staticmethod
    def _extract_stacktrace(exc_info: Any) -> str | None:
        etype, evalue, etb = exc_info
        try:
            return "".join(traceback.format_exception(etype, evalue, etb))
        except Exception:
            return None

    @staticmethod
    def _build_summary(exc_type: str | None, exc_message: str | None) -> str | None:
        if exc_type and exc_message:
            return f"{exc_type}: {exc_message}"
        return exc_type or exc_message

    # --------------------------------------------------------------------------
    # Main API
    # --------------------------------------------------------------------------
    @staticmethod
    def extract(record: LogRecord) -> dict[str, str | None]:
        """
        Extract and format exception information from a LogRecord.

        This function MUST NOT raise under any circumstance.
        """
        exc_info = getattr(record, "exc_info", None)

        # Fast path: no exception information attached to the record
        if not exc_info:
            return {
                "exception_summary": None,
                "exception_type": None,
                "exception_message": None,
                "exception_stacktrace": None,
            }

        try:
            exc_type, exc_message = ExceptionProcessor._extract_basic_info(exc_info)
            stack = ExceptionProcessor._extract_stacktrace(exc_info)
            summary = ExceptionProcessor._build_summary(exc_type, exc_message)

            return {
                "exception_summary": summary,
                "exception_type": exc_type,
                "exception_message": exc_message,
                "exception_stacktrace": stack,
            }

        except Exception:
            # Defensive fallback: even if extraction crashes,
            # never break the logging pipeline.
            _EXCEPTION_EXTRACTION_FAILURES.inc()

            return {
                "exception_summary": "exception block extraction failed",
                "exception_type": "ExtractionFailure",
                "exception_message": None,
                "exception_stacktrace": None,
            }
