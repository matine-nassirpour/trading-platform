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
from quantum.infrastructure.observability.logging.sinks.files.partitioned_handler import (
    PartitionedJSONLFileHandler,
)


class HandlerFactory:
    """
    Pure handler factory.
    All handlers returned are fully configured (formatter + pipeline).
    """

    def __init__(
        self,
        bundle: LoggingRuntimeBundle,
        formatter: JsonFormatter,
        pipeline: LoggingPipeline,
    ):
        self.bundle = bundle
        self.formatter = formatter
        self.pipeline = pipeline

    def _attach(self, handler, level=None):
        handler.setLevel(level or self.bundle.log_level)
        handler.setFormatter(self.formatter)
        handler.addFilter(self.pipeline)
        return handler

    def console(self):
        h = logging.StreamHandler()
        return self._attach(h)

    def partitioned(self):
        h = PartitionedJSONLFileHandler(bundle=self.bundle)
        return self._attach(h)
