import logging

from pathlib import Path

from quantum.infrastructure.observability.logging.formatters.json_formatter import (
    JsonFormatter,
)
from quantum.infrastructure.observability.logging.metadata.config_bundle import (
    LoggingRuntimeBundle,
)
from quantum.infrastructure.observability.logging.pipeline.engine.pipeline import (
    LoggingPipeline,
)
from quantum.infrastructure.observability.logging.sinks.filesystem.formatters.jsonl_formatter import (
    RecordFormatter,
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
        self, handler: logging.Handler, level: int | None = None
    ) -> logging.Handler:
        handler.setLevel(level or self._bundle.log_level)
        handler.setFormatter(self._formatter)
        handler.addFilter(self._pipeline)
        return handler

    def console(self) -> logging.Handler:
        """Return a fully configured console handler."""
        handler = logging.StreamHandler()
        return self._attach(handler)

    def partitioned(self) -> logging.Handler:
        """Return a fully configured partitioned JSONL file handler."""
        policy = PartitionPolicy(
            base_dir=Path(self._bundle.log_dir),
            env=self._bundle.env,
            namespace=self._bundle.namespace,
            app=self._bundle.app_name,
            max_bytes=self._bundle.log_max_bytes,
        )

        handler = PartitionedJSONLFileHandler(
            formatter=RecordFormatter(), policy=policy
        )

        return self._attach(handler)
