import logging
import os
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
from quantum.shared.config.env_flags import get_bool


class LoggingConfig:
    def __init__(
        self,
        app_name: str,
        environment: str,
        log_level: str = "INFO",
        namespace: str = "default",
        app_version: str | None = None,
    ) -> None:
        self.app_name = app_name
        self.environment = environment
        self.log_level = log_level
        self.namespace = namespace
        self.app_version = app_version


def close_and_remove_all_handlers(logger: logging.Logger) -> None:
    """
    Cleanly closes and then detaches all handlers from a logger.
    Idempotent and fault-tolerant (protected flush/close/remove).
    """
    for h in list(logger.handlers):
        # flush before close if possible
        flush = getattr(h, "flush", None)
        if callable(flush):
            with suppress(OSError, ValueError, RuntimeError, TypeError):
                flush()
        # close handler (bad FD/state may raise)
        with suppress(OSError, ValueError, RuntimeError, TypeError):
            h.close()
        # removeHandler raises ValueError if not attached
        with suppress(ValueError):
            logger.removeHandler(h)


def init_logging(cfg: LoggingConfig) -> None:
    # Common log level (root)
    level = getattr(logging, cfg.log_level.upper(), logging.INFO)

    def _add_base_filters(handler: logging.Handler, env: str) -> None:
        handler.addFilter(LoggingContextFilter(env=env))
        handler.addFilter(IgnoreLibrariesFilter())
        handler.addFilter(MonotonicTimestampFilter())
        handler.addFilter(RedactFilter())
        handler.addFilter(
            StaticFieldsFilter(
                service_name=cfg.app_name,
                service_namespace=cfg.namespace,
                service_version=(
                    cfg.app_version or os.getenv("QUANTUM_APP_VERSION", "0.0.0")
                ),
            )
        )

    # Parse env for rate limiting & sampling
    enable_rate_limit = get_bool("QUANTUM_LOG_RATELIMIT", default=False)
    try:
        rate_limit_rps = float(os.getenv("QUANTUM_LOG_RPS", "100"))
        if rate_limit_rps <= 0:
            enable_rate_limit = False
    except (TypeError, ValueError):
        enable_rate_limit = False
        rate_limit_rps = 100.0

    sample_info_every_env = os.getenv("QUANTUM_LOG_SAMPLE_INFO", "").strip()
    enable_info_sampling = False
    sample_info_every = 10
    if sample_info_every_env:
        try:
            sample_info_every = int(sample_info_every_env)
            enable_info_sampling = sample_info_every > 1
        except (TypeError, ValueError):
            enable_info_sampling = False

    def _maybe_add_ratelimit_and_sampling(
        handler: logging.Handler, *, allow_sampling: bool
    ) -> None:
        # Rate limit applies to all levels, including bursty WARNING/ERROR
        if enable_rate_limit:
            handler.addFilter(RateLimitFilter(max_per_sec=rate_limit_rps))
        # INFO sampling only if explicitly allowed (never for audit)
        if allow_sampling and enable_info_sampling:
            handler.addFilter(InfoSamplerFilter(sample_every=sample_info_every))

    root_logger = logging.getLogger()
    if root_logger.handlers:
        close_and_remove_all_handlers(root_logger)

    # Console handler (stderr) in JSON format
    stderr_handler = logging.StreamHandler(sys.stderr)
    stderr_handler.setLevel(level)
    stderr_handler.setFormatter(JsonFormatter())
    _add_base_filters(stderr_handler, cfg.environment)
    _maybe_add_ratelimit_and_sampling(stderr_handler, allow_sampling=True)

    partition_handler: logging.Handler | None = None

    # Partitioned JSONL (ENV opt-in)
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
        _add_base_filters(partition_handler, cfg.environment)
        _maybe_add_ratelimit_and_sampling(partition_handler, allow_sampling=True)

    # Build the definitive handler list (only non-None)
    handlers: list[logging.Handler] = [stderr_handler]
    if partition_handler is not None:
        handlers.append(partition_handler)

    root_logger.setLevel(level)
    for h in handlers:
        root_logger.addHandler(h)
    root_logger.propagate = False

    # AUDIT: handler independent of root (always captured)
    audit_base = os.getenv("QUANTUM_AUDIT_DIR")  # e.g. /var/log/quantum/audit
    if audit_base:
        audit_handler = AuditEventFileHandler(
            base_dir=audit_base,
            app=cfg.app_name,
            environment=cfg.environment,
            namespace=cfg.namespace,
        )
        # Handler level: NOTSET → do not filter here (we want to capture EVERYTHING on the audit side)
        audit_handler.setLevel(logging.NOTSET)
        # No formatter: we write the raw "event" payload (already structured)
        _add_base_filters(audit_handler, cfg.environment)
        audit_handler.addFilter(AuditEventFilter())
        # Intentionally: no RateLimitFilter / InfoSamplerFilter here

        # Attach the handler directly to the structured event logger
        # (used by emit_event). Set it to DEBUG to allow all levels to pass.
        audit_logger = logging.getLogger("quantum.trading")

        # Avoid duplicates when re-initing: remove any existing AuditEventFileHandler
        # before adding the new one (and close properly).
        for h in list(audit_logger.handlers):
            if isinstance(h, AuditEventFileHandler):
                with suppress(OSError, ValueError, RuntimeError, TypeError):
                    h.flush() if hasattr(h, "flush") else None
                with suppress(OSError, ValueError, RuntimeError, TypeError):
                    h.close()
                with suppress(ValueError):
                    audit_logger.removeHandler(h)

        audit_logger.addHandler(audit_handler)
        audit_logger.setLevel(logging.DEBUG)  # does not filter by level

    # Route Python warnings → logging (console JSON)
    with suppress(AttributeError, RuntimeError):
        logging.captureWarnings(True)
