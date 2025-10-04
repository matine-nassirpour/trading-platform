import logging
import os
import sys

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


def init_logging(cfg: LoggingConfig) -> None:
    # Common log level
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
    enable_rate_limit = os.getenv("QUANTUM_LOG_RATELIMIT", "0") == "1"
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

    # Console handler (stderr) in JSON format
    stderr_handler = logging.StreamHandler(sys.stderr)
    stderr_handler.setLevel(level)
    stderr_handler.setFormatter(JsonFormatter())
    _add_base_filters(stderr_handler, cfg.environment)
    _maybe_add_ratelimit_and_sampling(stderr_handler, allow_sampling=True)

    partition_handler: logging.Handler | None = None
    audit_handler: logging.Handler | None = None

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

    # Audit per-event files (ENV opt-in)
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
        _add_base_filters(audit_handler, cfg.environment)
        audit_handler.addFilter(AuditEventFilter())
        # Intentionally: no RateLimitFilter / InfoSamplerFilter here

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
