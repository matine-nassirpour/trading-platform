import logging
import sys
from contextlib import suppress

from quantum.core.config.models.core import CoreSettings
from quantum.core.config.models.logging import LoggingSettings
from quantum.infrastructure.observability.logging.filters.audit_event_filter import (
    AuditEventFilter,
)
from quantum.infrastructure.observability.logging.filters.context_filter import (
    LoggingContextFilter,
)
from quantum.infrastructure.observability.logging.filters.ignore_libraries_filter import (
    IgnoreLibrariesFilter,
)
from quantum.infrastructure.observability.logging.filters.info_sampler_filter import (
    InfoSamplerFilter,
)
from quantum.infrastructure.observability.logging.filters.monotonic_timestamp_filter import (
    MonotonicTimestampFilter,
)
from quantum.infrastructure.observability.logging.filters.rate_limit_filter import (
    RateLimitFilter,
)
from quantum.infrastructure.observability.logging.filters.redact_filter import (
    RedactFilter,
)
from quantum.infrastructure.observability.logging.filters.static_fields_filter import (
    StaticFieldsFilter,
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


def close_and_remove_all_handlers(logger: logging.Logger) -> None:
    """
    Cleanly closes and detaches all handlers from a logger.
    Idempotent and fault-tolerant (protected flush/close/remove).
    """
    for h in list(logger.handlers):
        flush = getattr(h, "flush", None)
        if callable(flush):
            with suppress(OSError, ValueError, RuntimeError, TypeError):
                flush()
        with suppress(OSError, ValueError, RuntimeError, TypeError):
            h.close()
        with suppress(ValueError):
            logger.removeHandler(h)


def init_logging(
    core_settings: CoreSettings, logging_settings: LoggingSettings
) -> None:
    """
    Initializes structured JSON logging, audit file sinks, and optional rate limiting.
    """
    level = getattr(logging, logging_settings.quantum_log_level.upper(), logging.INFO)

    # ─── Reset any existing handlers (idempotent re-init)
    root_logger = logging.getLogger()
    if root_logger.handlers:
        close_and_remove_all_handlers(root_logger)

    # ─── Common filters for all handlers
    def _add_base_filters(handler: logging.Handler) -> None:
        handler.addFilter(LoggingContextFilter(env=core_settings.quantum_env))
        handler.addFilter(IgnoreLibrariesFilter())
        handler.addFilter(MonotonicTimestampFilter())
        handler.addFilter(RedactFilter())
        handler.addFilter(
            StaticFieldsFilter(
                service_name=core_settings.quantum_app_name,
                service_namespace=core_settings.quantum_ns,
                service_version=core_settings.quantum_app_version,
            )
        )

    # ─── Optional dynamic filters (rate limiting & sampling)
    def _maybe_add_ratelimit_and_sampling(
        handler: logging.Handler, *, allow_sampling: bool
    ) -> None:
        if logging_settings.quantum_log_ratelimit:
            handler.addFilter(
                RateLimitFilter(max_per_sec=logging_settings.quantum_log_rps)
            )
        if allow_sampling and logging_settings.quantum_log_sample_info > 1:
            handler.addFilter(
                InfoSamplerFilter(sample_every=logging_settings.quantum_log_sample_info)
            )

    # ─── Console handler (stderr)
    stderr_handler = logging.StreamHandler(sys.stderr)
    stderr_handler.setLevel(level)
    stderr_handler.setFormatter(JsonFormatter())
    _add_base_filters(stderr_handler)
    _maybe_add_ratelimit_and_sampling(stderr_handler, allow_sampling=True)

    handlers: list[logging.Handler] = [stderr_handler]

    # ─── Partitioned JSONL handler
    if logging_settings.quantum_log_dir:
        partition_handler = PartitionedJSONLFileHandler(core_settings, logging_settings)
        partition_handler.setLevel(level)
        partition_handler.setFormatter(JsonFormatter())
        _add_base_filters(partition_handler)
        _maybe_add_ratelimit_and_sampling(partition_handler, allow_sampling=True)
        handlers.append(partition_handler)

    # ─── Apply handlers
    root_logger.setLevel(level)
    for h in handlers:
        root_logger.addHandler(h)
    root_logger.propagate = False

    # ─── Audit sink
    if logging_settings.quantum_audit_dir:
        audit_logger = logging.getLogger("quantum.trading")

        for h in list(audit_logger.handlers):
            if isinstance(h, AuditEventFileHandler):
                with suppress(OSError, ValueError, RuntimeError, TypeError):
                    h.flush() if hasattr(h, "flush") else None
                with suppress(OSError, ValueError, RuntimeError, TypeError):
                    h.close()
                with suppress(ValueError):
                    audit_logger.removeHandler(h)

        audit_handler = AuditEventFileHandler(
            base_dir=logging_settings.quantum_audit_dir,
            app=core_settings.quantum_app_name,
            environment=core_settings.quantum_env,
            namespace=core_settings.quantum_ns,
        )
        audit_handler.setLevel(logging.NOTSET)
        _add_base_filters(audit_handler)
        audit_handler.addFilter(AuditEventFilter())
        audit_logger.addHandler(audit_handler)
        audit_logger.setLevel(logging.DEBUG)  # does not filter by level

    # ─── Python warnings → logging
    with suppress(AttributeError, RuntimeError):
        logging.captureWarnings(True)
