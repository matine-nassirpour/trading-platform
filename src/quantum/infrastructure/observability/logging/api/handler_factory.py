import logging

from quantum.infrastructure.observability.logging.formatters.json_formatter import (
    JsonFormatter,
)
from quantum.infrastructure.observability.logging.metadata.config_bundle import (
    LoggingRuntimeBundle,
)
from quantum.infrastructure.observability.logging.pipeline.engine.pipeline import (
    LoggingPipeline,
)
from quantum.infrastructure.observability.logging.sinks.filesystem.partitioned_handler import (
    PartitionedJSONLFileHandler,
)


class HandlerFactory:
    """
    Pure handler factory.
    All handlers returned are fully configured (formatter + pipeline).
    No logger manipulation. No side effects.
    """

    def __init__(
        self,
        bundle: LoggingRuntimeBundle,
        formatter: JsonFormatter,
        pipeline: LoggingPipeline,
    ) -> None:
        self._bundle = bundle
        self._formatter = formatter
        self._pipeline = pipeline

    def _attach(
        self, handler: logging.Handler, level: int | None = None
    ) -> logging.Handler:
        handler.setLevel(level or self._bundle.log_level)
        handler.setFormatter(self._formatter)
        handler.addFilter(self._pipeline)
        return handler

    def console(self) -> logging.Handler:
        """Return a fully configured console handler."""
        h = logging.StreamHandler()
        return self._attach(h)

    def partitioned(self) -> logging.Handler:
        """Return a fully configured partitioned JSONL file handler."""
        h = PartitionedJSONLFileHandler(bundle=self._bundle)
        return self._attach(h)
