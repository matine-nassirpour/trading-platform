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
from quantum.infrastructure.observability.logging.formatting.pretty_json_formatter import (
    PrettyJsonFormatter,
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

    # ------------------------------------------------------------------
    # Internal helper
    # ------------------------------------------------------------------
    def _attach(
        self,
        handler: logging.Handler,
        *,
        level: int | None = None,
        formatter: logging.Formatter | None = None,
    ) -> logging.Handler:
        """
        Attach:
        - log level
        - unified pipeline filter
        - optional explicit formatter
        """

        handler.setLevel(level or self._bundle.log_level)

        if formatter is not None:
            handler.setFormatter(formatter)
        else:
            handler.setFormatter(self._formatter)

        handler.addFilter(self._pipeline)
        return handler

    # --------------------------------------------------------------------------
    # Console handler (Pretty or compact JSON)
    # --------------------------------------------------------------------------
    def console(self) -> logging.Handler:
        """
        Return a console handler with PrettyJsonFormatter (human-readable)
        or JsonFormatter (compact) depending on configuration.
        """
        handler = logging.StreamHandler()

        formatter = (
            PrettyJsonFormatter(self._bundle.identity.instance_id)
            if self._bundle.enable_pretty_console
            else self._formatter
        )

        return self._attach(handler, formatter=formatter)

    # --------------------------------------------------------------------------
    # Partitioned JSONL file handler (structured machine output)
    # --------------------------------------------------------------------------
    def partitioned(self) -> logging.Handler:
        """
        Return a fully configured partitioned JSONL file handler.
        Formatter is internal to handler; no external formatter attached.
        """
        policy = PartitionPolicy(
            base_dir=self._bundle.log_dir,
            env=self._bundle.identity.environment,
            namespace=self._bundle.identity.service_namespace,
            app=self._bundle.identity.service_name,
            max_bytes=self._bundle.log_max_bytes,
        )

        formatter = JSONLFormatter(instance_id=self._bundle.identity.instance_id)
        handler = PartitionedJSONLFileHandler(formatter=formatter, policy=policy)

        # handler has its own internal formatter → no external logging.Formatter attached
        return self._attach(handler, formatter=None)
