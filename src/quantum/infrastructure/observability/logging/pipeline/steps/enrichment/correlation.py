import logging

from quantum.infrastructure.observability.context.context_attributes_provider import (
    ContextAttributesProvider,
)
from quantum.infrastructure.observability.logging.pipeline.engine.step import (
    PipelineStep,
)


class CorrelationStep(PipelineStep):
    """Injects correlation_id and run_id using a unified context provider."""

    def process(self, record: logging.LogRecord) -> bool:
        ctx = ContextAttributesProvider.get().as_dict()

        if "correlation_id" not in record.__dict__:
            record.correlation_id = ctx.get("correlation_id")

        if "run_id" not in record.__dict__:
            record.run_id = ctx.get("run_id")

        return True
