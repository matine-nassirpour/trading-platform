from __future__ import annotations

import logging

from quantum.application.ports.outbound.logging_port import LoggingPort
from quantum.infrastructure.observability.logging.api.event_emitter import emit_event


class LoggingDriver(LoggingPort):
    """Concrete implementation of LoggingPort using Quantum's observability stack."""

    def __init__(self) -> None:
        self._logger = logging.getLogger("quantum.logging.driver")

    def emit_info(self, message: str, **attrs: object) -> None:
        """
        Emit an INFO-level structured log message deterministically,
        with proper redaction via each handler’s formatter chain.
        """
        try:
            record = logging.LogRecord(
                name="quantum.logging.driver",
                level=logging.INFO,
                pathname=__file__,
                lineno=0,
                msg=message,
                args=(),
                exc_info=None,
                func=None,
            )
            record.attrs = attrs

            root_logger = logging.getLogger()
            for h in root_logger.handlers:
                try:
                    h.acquire()

                    # Apply each handler's filter chain manually
                    for flt in getattr(h, "filters", []):
                        if not flt.filter(record):
                            break

                    # Apply formatter if present (for redaction, schema)
                    fmt = getattr(h, "formatter", None)
                    if fmt:
                        try:
                            fmt.format(record)  # triggers formatter/redactor logic
                        except Exception as exc:
                            self._logger.debug(
                                "Formatter '%s' failed to process log record (%s): %s",
                                getattr(fmt, "__class__", type(fmt)).__name__,
                                getattr(record, "msg", "<no message>"),
                                exc,
                                exc_info=True,
                            )

                    # Emit directly to handler (thread-safe, deterministic)
                    h.emit(record)
                    if hasattr(h, "flush"):
                        h.flush()
                finally:
                    h.release()

        except Exception as exc:
            logging.getLogger(__name__).warning("emit_info failed: %s", exc)

    def emit_event(self, payload: dict[str, object]) -> None:
        """Emit an audit/telemetry event via the event emitter."""
        try:
            emit_event(payload)
        except Exception as exc:
            self._logger.warning("Failed to emit event: %s", exc)
