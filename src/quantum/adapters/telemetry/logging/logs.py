import logging
import sys

from quantum.adapters.telemetry.logging.filters import (
    IgnoreLibrariesFilter,
    LoggingContextFilter,
    SchemaVersionFilter,
)
from quantum.adapters.telemetry.logging.formatter import JsonFormatter


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
        handler.addFilter(SchemaVersionFilter())

    # Console handler (stderr) in JSON format
    stderr_handler = logging.StreamHandler(sys.stderr)
    stderr_handler.setLevel(level)
    stderr_handler.setFormatter(JsonFormatter())
    _add_filters(stderr_handler, cfg.environment)

    # Root logger: clear all existing handlers
    root_logger = logging.getLogger()
    if root_logger.hasHandlers():
        root_logger.handlers.clear()

    root_logger.setLevel(level)
    root_logger.addHandler(stderr_handler)
    root_logger.propagate = False
