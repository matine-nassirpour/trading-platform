import logging

from contextlib import suppress

from quantum.infrastructure.observability.logging.api.handler_factory import (
    HandlerFactory,
)
from quantum.infrastructure.observability.logging.audit.filter import AuditEventFilter
from quantum.infrastructure.observability.logging.audit.sink_handler import (
    AuditEventFileHandler,
)
from quantum.infrastructure.observability.logging.formatters.json_formatter import (
    JsonFormatter,
)
from quantum.infrastructure.observability.logging.metadata.config_bundle import (
    LoggingRuntimeBundle,
)
from quantum.infrastructure.observability.logging.pipeline.engine.factory import (
    LoggingPipelineFactory,
)


class LoggingBuilder:
    """
    Responsible ONLY for assembling handlers and sinks.
    No global state manipulation and no direct root logger access.
    """

    def __init__(self, bundle: LoggingRuntimeBundle):
        self.bundle = bundle
        self.pipeline = LoggingPipelineFactory.build(bundle.pipeline_config, bundle)
        self.formatter = JsonFormatter(bundle.instance_id)
        self.factory = HandlerFactory(bundle, self.formatter, self.pipeline)

    # --------------------------------------------------------------------------
    # Application handlers
    # --------------------------------------------------------------------------
    def build_handlers(self):
        handlers = []

        if self.bundle.enable_console_handler:
            handlers.append(self.factory.console())

        if self.bundle.enable_partition_handler and self.bundle.log_dir:
            handlers.append(self.factory.partitioned())

        return handlers

    # --------------------------------------------------------------------------
    # Audit sink
    # --------------------------------------------------------------------------
    def configure_audit_sink(self) -> None:
        if not self.bundle.audit_dir:
            return

        audit_logger = logging.getLogger("quantum.trading.audit")

        # wipe previous
        for h in list(audit_logger.handlers):
            with suppress(Exception):
                if hasattr(h, "flush"):
                    h.flush()
            with suppress(Exception):
                h.close()
            with suppress(Exception):
                audit_logger.removeHandler(h)

        handler = AuditEventFileHandler(
            base_dir=self.bundle.audit_dir,
            env=self.bundle.env,
            namespace=self.bundle.namespace,
            app=self.bundle.app_name,
        )
        handler.setLevel(logging.NOTSET)
        handler.setFormatter(self.formatter)
        handler.addFilter(AuditEventFilter(allowlist=self.bundle.audit_allowlist))

        audit_logger.addHandler(handler)
        audit_logger.setLevel(logging.DEBUG)
        audit_logger.propagate = False
