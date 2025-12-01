import logging

from contextlib import suppress
from typing import Final

from quantum.infrastructure.observability.foundation.config.logging_runtime_bundle import (
    LoggingRuntimeBundle,
)
from quantum.infrastructure.observability.logging.api.handler_factory import (
    HandlerFactory,
)
from quantum.infrastructure.observability.logging.audit.filter import AuditEventFilter
from quantum.infrastructure.observability.logging.formatting.json_formatter import (
    JsonFormatter,
)
from quantum.infrastructure.observability.logging.pipeline.engine.factory import (
    LoggingPipelineFactory,
)
from quantum.infrastructure.observability.logging.sinks.filesystem.handlers.audit_event_file_handler import (
    AuditEventFileHandler,
)

AUDIT_LOGGER: Final = logging.getLogger("quantum.audit")


class LoggingBuilder:
    """
    Assembles handlers and audit sinks from immutable runtime configuration.
    No global state manipulation and no direct root logger access.
    """

    def __init__(self, bundle: LoggingRuntimeBundle) -> None:
        self._bundle = bundle
        self._pipeline = LoggingPipelineFactory.build(bundle.pipeline_config, bundle)
        self._formatter = JsonFormatter(bundle.instance_id)
        self._factory = HandlerFactory(bundle, self._formatter, self._pipeline)

    # --------------------------------------------------------------------------
    # Application handlers
    # --------------------------------------------------------------------------
    def build_handlers(self) -> list[logging.Handler]:
        """Build and return a list of fully configured handlers."""
        handlers: list[logging.Handler] = []

        if self._bundle.enable_console_handler:
            handlers.append(self._factory.console())

        if self._bundle.enable_partition_handler and self._bundle.log_dir:
            handlers.append(self._factory.partitioned())

        return handlers

    # --------------------------------------------------------------------------
    # Audit sink
    # --------------------------------------------------------------------------
    def configure_audit_sink(self) -> None:
        """Reset and configure the dedicated audit logger sink."""
        if not self._bundle.audit_dir:
            return

        # Reset existing handlers
        for h in list(AUDIT_LOGGER.handlers):
            with suppress(Exception):
                if hasattr(h, "flush"):
                    h.flush()
            with suppress(Exception):
                h.close()
            with suppress(Exception):
                AUDIT_LOGGER.removeHandler(h)

        handler = AuditEventFileHandler(
            base_dir=self._bundle.audit_dir,
            env=self._bundle.environment,
            namespace=self._bundle.service_namespace,
            app=self._bundle.service_name,
        )
        handler.setLevel(logging.NOTSET)
        handler.setFormatter(self._formatter)
        handler.addFilter(AuditEventFilter(allowlist=self._bundle.audit_allowlist))

        AUDIT_LOGGER.addHandler(handler)
        AUDIT_LOGGER.setLevel(logging.DEBUG)
        AUDIT_LOGGER.propagate = False
