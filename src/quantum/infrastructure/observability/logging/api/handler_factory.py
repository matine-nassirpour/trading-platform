import logging

from quantum.infrastructure.observability.foundation.config.logging_runtime_bundle import (
    LoggingRuntimeBundle,
)
from quantum.infrastructure.observability.logging.formatting.json_formatter import (
    JsonFormatter,
)
from quantum.infrastructure.observability.logging.formatting.jsonl_formatter import (
    JSONLFormatter,
)
from quantum.infrastructure.observability.logging.pipeline.engine.pipeline import (
    LoggingPipeline,
)
from quantum.infrastructure.observability.logging.sinks.filesystem.handlers.partitioned_jsonl_file_handler import (
    PartitionedJSONLFileHandler,
)
from quantum.infrastructure.observability.logging.sinks.filesystem.policies.partition_policy import (
    PartitionPolicy,
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
        self, handler: logging.Handler, *, add_formatter: bool, level: int | None = None
    ) -> logging.Handler:
        """Attach level + pipeline filter."""

        handler.setLevel(level or self._bundle.log_level)

        if add_formatter:
            handler.setFormatter(self._formatter)

        handler.addFilter(self._pipeline)
        return handler

    def console(self) -> logging.Handler:
        """Return a fully configured console handler."""
        handler = logging.StreamHandler()
        return self._attach(handler, add_formatter=True)

    def partitioned(self) -> logging.Handler:
        """Return a fully configured partitioned JSONL file handler."""
        policy = PartitionPolicy(
            base_dir=self._bundle.log_dir,
            env=self._bundle.environment,
            namespace=self._bundle.service_namespace,
            app=self._bundle.service_name,
            max_bytes=self._bundle.log_max_bytes,
        )

        formatter = JSONLFormatter(instance_id=self._bundle.instance_id)

        handler = PartitionedJSONLFileHandler(formatter=formatter, policy=policy)

        # handler has its own internal formatter → no external logging.Formatter attached
        return self._attach(handler, add_formatter=False)
