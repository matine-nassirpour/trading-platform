import logging
import sys
from contextlib import suppress

from quantum.infrastructure.observability.logging.audit_sink import (
    AuditEventFileHandler,
)
from quantum.infrastructure.observability.logging.filters import (
    AuditEventFilter,
    IgnoreLibrariesFilter,
    InfoSamplerFilter,
    LoggingContextFilter,
    MonotonicTimestampFilter,
    RateLimitFilter,
    RedactFilter,
    StaticFieldsFilter,
)
from quantum.infrastructure.observability.logging.formatter import JsonFormatter
from quantum.infrastructure.observability.logging.partitioned_handlers import (
    PartitionedJSONLFileHandler,
)
from quantum.shared.config.config_manager import Settings
from quantum.shared.config.observability_settings import ObservabilitySettings


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


def init_logging(settings: Settings, observability: ObservabilitySettings) -> None:
    """
    Initializes structured JSON logging, audit file sinks, and optional rate limiting.
    """
    level = getattr(logging, observability.quantum_log_level.upper(), logging.INFO)

    # ─── Reset any existing handlers (idempotent re-init)
    root_logger = logging.getLogger()
    if root_logger.handlers:
        close_and_remove_all_handlers(root_logger)

    # ─── Common filters for all handlers
    def _add_base_filters(handler: logging.Handler) -> None:
        handler.addFilter(LoggingContextFilter(env=settings.quantum_env))
        handler.addFilter(IgnoreLibrariesFilter())
        handler.addFilter(MonotonicTimestampFilter())
        handler.addFilter(RedactFilter())
        handler.addFilter(
            StaticFieldsFilter(
                service_name=settings.quantum_app_name,
                service_namespace=settings.quantum_ns,
                service_version=settings.quantum_app_version,
            )
        )

    # ─── Optional dynamic filters (rate limiting & sampling)
    def _maybe_add_ratelimit_and_sampling(
        handler: logging.Handler, *, allow_sampling: bool
    ) -> None:
        if observability.quantum_log_ratelimit:
            handler.addFilter(
                RateLimitFilter(max_per_sec=observability.quantum_log_rps)
            )
        if allow_sampling and observability.quantum_log_sample_info > 1:
            handler.addFilter(
                InfoSamplerFilter(sample_every=observability.quantum_log_sample_info)
            )

    # ─── Console handler (stderr)
    stderr_handler = logging.StreamHandler(sys.stderr)
    stderr_handler.setLevel(level)
    stderr_handler.setFormatter(JsonFormatter())
    _add_base_filters(stderr_handler)
    _maybe_add_ratelimit_and_sampling(stderr_handler, allow_sampling=True)

    handlers: list[logging.Handler] = [stderr_handler]

    # ─── Partitioned JSONL handler
    if observability.quantum_log_dir:
        partition_handler = PartitionedJSONLFileHandler(
            base_dir=observability.quantum_log_dir,
            app=settings.quantum_app_name,
            environment=settings.quantum_env,
            namespace=settings.quantum_ns,
        )
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
    if observability.quantum_audit_dir:
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
            base_dir=observability.quantum_audit_dir,
            app=settings.quantum_app_name,
            environment=settings.quantum_env,
            namespace=settings.quantum_ns,
        )
        audit_handler.setLevel(logging.NOTSET)
        _add_base_filters(audit_handler)
        audit_handler.addFilter(AuditEventFilter())
        audit_logger.addHandler(audit_handler)
        audit_logger.setLevel(logging.DEBUG)  # does not filter by level

    # ─── Python warnings → logging
    with suppress(AttributeError, RuntimeError):
        logging.captureWarnings(True)
