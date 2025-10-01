import logging
import os
import sys

from quantum.infrastructure.observability.logging.audit_sink import (
    AuditEventFileHandler,
)
from quantum.infrastructure.observability.logging.filters import (
    AuditEventFilter,
    IgnoreLibrariesFilter,
    LoggingContextFilter,
    MonotonicTimestampFilter,
)
from quantum.infrastructure.observability.logging.formatter import JsonFormatter
from quantum.infrastructure.observability.logging.partitioned_handlers import (
    PartitionedJSONLFileHandler,
)


class LoggingConfig:
    def __init__(
        self,
        app_name: str,
        environment: str,
        log_level: str = "INFO",
        namespace: str = "default",
    ) -> None:
        self.app_name = app_name
        self.environment = environment
        self.log_level = log_level
        self.namespace = namespace


def init_logging(cfg: LoggingConfig) -> None:
    # Common log level
    level = getattr(logging, cfg.log_level.upper(), logging.INFO)

    def _add_filters(handler: logging.Handler, env: str) -> None:
        handler.addFilter(LoggingContextFilter(env=env))
        handler.addFilter(IgnoreLibrariesFilter())
        handler.addFilter(MonotonicTimestampFilter())

    # Console handler (stderr) in JSON format
    stderr_handler = logging.StreamHandler(sys.stderr)
    stderr_handler.setLevel(level)
    stderr_handler.setFormatter(JsonFormatter())
    _add_filters(stderr_handler, cfg.environment)

    partition_handler: logging.Handler | None = None
    audit_handler: logging.Handler | None = None

    # Partitioned JSONL (ENV opt-in)d
    partition_base = os.getenv("QUANTUM_LOG_DIR")  # e.g. /var/log/quantum
    if partition_base:
        partition_handler = PartitionedJSONLFileHandler(
            base_dir=partition_base,
            app=cfg.app_name,
            environment=cfg.environment,
            namespace=cfg.namespace,
        )
        partition_handler.setLevel(level)
        partition_handler.setFormatter(JsonFormatter())
        _add_filters(partition_handler, cfg.environment)

    # Audit per-event files (ENV opt-in) ---
    audit_base = os.getenv("QUANTUM_AUDIT_DIR")  # e.g. /var/log/quantum/audit
    if audit_base:
        audit_handler = AuditEventFileHandler(
            base_dir=audit_base,
            app=cfg.app_name,
            environment=cfg.environment,
            namespace=cfg.namespace,
        )
        # No formatter: we write the raw 'event' payload (already structured Pydantic)
        audit_handler.setLevel(level)
        _add_filters(audit_handler, cfg.environment)
        audit_handler.addFilter(AuditEventFilter())

    # Root logger: clear all existing handlers
    root_logger = logging.getLogger()
    if root_logger.hasHandlers():
        root_logger.handlers.clear()

    # Build the definitive handler list (only non-None)
    handlers: list[logging.Handler] = [stderr_handler]
    if partition_handler is not None:
        handlers.append(partition_handler)
    if audit_handler is not None:
        handlers.append(audit_handler)

    root_logger.setLevel(level)
    for h in handlers:
        root_logger.addHandler(h)

    root_logger.propagate = False
