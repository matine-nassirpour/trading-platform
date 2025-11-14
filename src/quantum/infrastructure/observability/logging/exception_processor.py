import traceback

from typing import Final

EXCEPTION_FIELD_NAMES: Final[set[str]] = {
    "exception",
    "exception_type",
    "exception_message",
    "exception_stacktrace",
}


class ExceptionProcessor:
    """
    Unified, deterministic and schema-safe exception block builder.

    This processor centralizes all exception extraction logic used by
    the structured logging system. It is the single source of truth for
    generating exception blocks consumed by LogPayloadV1 and fallback
    JSON payloads.

    Guarantees:
    - Stable field names
    - Deterministic output
    - Safe against recursive exceptions
    - No traceback formatting failures bubbling up
    """

    __slots__ = ()

    @staticmethod
    def extract(record) -> dict[str, str | None]:
        """Extract and format exception information from a LogRecord."""
        if not record.exc_info:
            return {
                "exception": None,
                "exception_type": None,
                "exception_message": None,
                "exception_stacktrace": None,
            }

        try:
            etype, evalue, etb = record.exc_info

            exc_type = getattr(etype, "__name__", str(etype)) if etype else None
            exc_message = str(evalue) if evalue is not None else None

            try:
                formatted = "".join(traceback.format_exception(etype, evalue, etb))
            except Exception:
                formatted = "exception formatting failed"

            return {
                "exception": formatted,
                "exception_type": exc_type,
                "exception_message": exc_message,
                "exception_stacktrace": formatted,
            }

        except Exception:
            # Defensive fallback: even if extraction crashes,
            # never break the logging pipeline.
            return {
                "exception": "exception block extraction failed",
                "exception_type": "Exception",
                "exception_message": None,
                "exception_stacktrace": None,
            }
