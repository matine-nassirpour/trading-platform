import logging
import sys

from contextlib import suppress

from quantum.infrastructure.observability.logging.config_bundle import (
    LoggingRuntimeBundle,
)
from quantum.infrastructure.observability.logging.filters.audit_event_filter import (
    AuditEventFilter,
)
from quantum.infrastructure.observability.logging.filters.info_sampler_filter import (
    InfoSamplerFilter,
)
from quantum.infrastructure.observability.logging.filters.rate_limit_filter import (
    RateLimitFilter,
)
from quantum.infrastructure.observability.logging.formatters.json_formatter import (
    JsonFormatter,
)
from quantum.infrastructure.observability.logging.handlers.audit_sink_handler import (
    AuditEventFileHandler,
)
from quantum.infrastructure.observability.logging.handlers.partitioned_handler import (
    PartitionedJSONLFileHandler,
)
from quantum.infrastructure.observability.logging.pipeline.factory import (
    LoggingPipelineFactory,
)


# ╭────────────────────────────────────────────────────────────────────────────╮
# │ Utilities                                                                  │
# ╰────────────────────────────────────────────────────────────────────────────╯
def close_and_remove_all_handlers(logger: logging.Logger) -> None:
    """
    Safely closes and detaches all handlers from a given logger.

    This operation is idempotent and fault-tolerant.
    It ensures a clean reinitialization of the logging subsystem
    without leaving open file descriptors or duplicate handlers.
    """
    for handler in list(logger.handlers):
        with suppress(Exception):
            if hasattr(handler, "flush"):
                handler.flush()
        with suppress(Exception):
            handler.close()
        with suppress(Exception):
            logger.removeHandler(handler)


# ╭────────────────────────────────────────────────────────────────────────────╮
# │ Internal Helpers                                                           │
# ╰────────────────────────────────────────────────────────────────────────────╯
def _apply_filters(handler: logging.Handler, bundle: LoggingRuntimeBundle) -> None:
    """Attach preprocessing filters."""
    pipeline = LoggingPipelineFactory.build(bundle.pipeline_config, bundle)
    handler.addFilter(pipeline)

    if bundle.sample_info_every > 1:
        handler.addFilter(InfoSamplerFilter(sample_every=bundle.sample_info_every))

    if bundle.ratelimit_rps and bundle.ratelimit_rps > 0:
        handler.addFilter(RateLimitFilter(max_per_sec=bundle.ratelimit_rps))


def _build_console_handler(bundle: LoggingRuntimeBundle) -> logging.Handler:
    handler = logging.StreamHandler(sys.stderr)
    handler.setLevel(bundle.log_level)
    handler.setFormatter(JsonFormatter(bundle.instance_id))
    _apply_filters(handler, bundle)

    return handler


def _build_partition_handler(bundle: LoggingRuntimeBundle) -> logging.Handler | None:
    """Create a partitioned JSONL file handler if enabled."""
    if not bundle.log_dir:
        return None

    if not bundle.enable_partition_handler:
        return None

    handler = PartitionedJSONLFileHandler(bundle=bundle)
    handler.setLevel(bundle.log_level)
    handler.setFormatter(JsonFormatter(bundle.instance_id))
    _apply_filters(handler, bundle)

    return handler


def _configure_audit_sink(bundle: LoggingRuntimeBundle) -> None:
    """Configure the audit-event file handler."""
    if not bundle.audit_dir:
        return

    audit_logger = logging.getLogger("quantum.trading")

    # Remove preexisting audit handlers
    for h in list(audit_logger.handlers):
        if isinstance(h, AuditEventFileHandler):
            with suppress(Exception):
                h.flush() if hasattr(h, "flush") else None
            with suppress(Exception):
                h.close()
            with suppress(Exception):
                audit_logger.removeHandler(h)

    # Create new handler
    handler = AuditEventFileHandler(
        base_dir=bundle.audit_dir,
        env=bundle.env,
        namespace=bundle.namespace,
        app=bundle.app_name,
    )
    handler.setLevel(logging.NOTSET)

    handler.addFilter(AuditEventFilter(allowlist=bundle.audit_allowlist))
    _apply_filters(handler, bundle)

    audit_logger.addHandler(handler)
    audit_logger.setLevel(logging.DEBUG)


# ╭────────────────────────────────────────────────────────────────────────────╮
# │ Public initializer                                                         │
# ╰────────────────────────────────────────────────────────────────────────────╯
def init_logging(bundle: LoggingRuntimeBundle) -> None:
    """Initialize the Quantum structured logging infrastructure."""
    # --------------------------------------------------------------------------
    # Reset root handlers
    # --------------------------------------------------------------------------
    root = logging.getLogger()
    close_and_remove_all_handlers(root)
    root.setLevel(bundle.log_level)
    root.propagate = False

    # --------------------------------------------------------------------------
    # Register handlers
    # --------------------------------------------------------------------------
    handlers: list[logging.Handler] = []

    if bundle.enable_console_handler:
        handlers.append(_build_console_handler(bundle))

    part = _build_partition_handler(bundle)
    if part:
        handlers.append(part)

    for h in handlers:
        root.addHandler(h)

    # --------------------------------------------------------------------------
    # Audit logger setup
    # --------------------------------------------------------------------------
    _configure_audit_sink(bundle)

    # --------------------------------------------------------------------------
    # Python warnings → logging redirection
    # --------------------------------------------------------------------------
    with suppress(Exception):
        logging.captureWarnings(True)
