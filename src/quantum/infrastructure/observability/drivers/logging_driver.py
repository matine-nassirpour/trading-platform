from __future__ import annotations

import logging

from collections.abc import Mapping, MutableMapping
from typing import Any, Final

from quantum.infrastructure.observability.logging.audit.emitter import (
    emit_event as _emit_audit_event,
)

# Application-level logger configured by init_logging()
APP_LOGGER: Final = logging.getLogger("quantum.app")
DRIVER_LOGGER: Final = logging.getLogger("quantum.logging.driver")


class LoggingDriver:
    """Concrete implementation of LoggingPort using Quantum's observability stack."""

    def __init__(self) -> None:
        # Emits through the fully configured Quantum application logger.
        self._logger = APP_LOGGER
        self._diag = DRIVER_LOGGER

    # --------------------------------------------------------------------------
    # Structured application logging
    # --------------------------------------------------------------------------
    def info(self, message: str, *, attrs: Mapping[str, Any] | None = None) -> None:
        """Emit a structured INFO‑level log event."""
        try:
            extra: MutableMapping[str, Any] = {}
            if attrs:
                # Defensive shallow copy; deeper sanitization is done by pipeline.
                extra["attrs"] = dict(attrs)

            # Full structured logging pipeline is invoked here.
            self._logger.info(message, extra=extra)
        except Exception as exc:
            self._diag.warning("info() emission failed: %s", exc, exc_info=True)

    # --------------------------------------------------------------------------
    # Generic structured logging entrypoint
    # --------------------------------------------------------------------------
    def log(
        self,
        level: int,
        message: str,
        *,
        attrs: Mapping[str, Any] | None = None,
    ) -> None:
        """
        Generic logging entrypoint.

        Ensures uniform entry into the structured logging pipeline regardless
        of severity. Equivalent to info()/debug()/etc., but useful for
        meta‑programming or adapters.
        """
        try:
            extra = {"attrs": dict(attrs)} if attrs else {}
            self._logger.log(level, message, extra=extra)
        except Exception as exc:
            self._diag.warning("log(level) failed: %s", exc, exc_info=True)

    # --------------------------------------------------------------------------
    # Audit event emission
    # --------------------------------------------------------------------------
    def emit_event(self, payload: Mapping[str, Any]) -> None:
        """Emit an audit/telemetry event via the event emitter."""
        try:
            _emit_audit_event(payload)
        except Exception as exc:
            self._diag.warning("emit_event() failed: %s", exc, exc_info=True)
