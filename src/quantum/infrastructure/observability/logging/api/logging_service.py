import logging

from contextlib import suppress

from quantum.infrastructure.observability.logging.api.logging_builder import (
    LoggingBuilder,
)
from quantum.infrastructure.observability.logging.metadata.config_bundle import (
    LoggingRuntimeBundle,
)


def close_and_remove_all_handlers(logger: logging.Logger) -> None:
    """Idempotent, safe reset of all handlers on a logger."""
    for handler in list(logger.handlers):
        with suppress(Exception):
            if hasattr(handler, "flush"):
                handler.flush()
        with suppress(Exception):
            handler.close()
        with suppress(Exception):
            logger.removeHandler(handler)


def init_logging(bundle: LoggingRuntimeBundle) -> None:
    """Public entrypoint for configuring the entire Quantum logging system."""

    # ─── Reset root handlers
    root = logging.getLogger()
    close_and_remove_all_handlers(root)
    root.setLevel(bundle.log_level)
    root.propagate = False

    builder = LoggingBuilder(bundle)

    # ─── Install all application handlers
    for handler in builder.build_handlers():
        root.addHandler(handler)

    builder.configure_audit_sink()

    # ─── Python warnings → logging redirection
    with suppress(Exception):
        logging.captureWarnings(True)
