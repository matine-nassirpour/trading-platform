import logging

from contextlib import suppress
from typing import Final

from quantum.infrastructure.observability.foundation.config.logging_runtime_bundle import (
    LoggingRuntimeBundle,
)
from quantum.infrastructure.observability.logging.api.logging_builder import (
    LoggingBuilder,
)

APP_LOGGER: Final = logging.getLogger("quantum.app")


def close_and_remove_all_handlers(logger: logging.Logger) -> None:
    """
    Idempotent, safe reset of all handlers on a given logger.
    Never touches parent loggers or the root logger.
    """
    for handler in list(logger.handlers):
        with suppress(Exception):
            if hasattr(handler, "flush"):
                handler.flush()
        with suppress(Exception):
            handler.close()
        with suppress(Exception):
            logger.removeHandler(handler)


def init_logging(bundle: LoggingRuntimeBundle) -> logging.Logger:
    """
    Public entrypoint for configuring the entire Quantum logging system.

    behavior:
    - Never uses or modifies the root logger.
    - All infrastructure logs go through a dedicated application logger.
    - Audit channel fully isolated.
    """

    # ─── Create the dedicated application logger
    APP_LOGGER.propagate = False  # NEVER bubble to root
    APP_LOGGER.setLevel(bundle.log_level)

    # Reset any previous configuration
    close_and_remove_all_handlers(APP_LOGGER)

    # ─── Build handlers (partitioned + console)
    builder = LoggingBuilder(bundle)

    for handler in builder.build_handlers():
        APP_LOGGER.addHandler(handler)

    builder.configure_audit_sink()

    # Disable Python warnings → root redirection unless explicitly enabled
    with suppress(Exception):
        logging.captureWarnings(False)

    return APP_LOGGER
