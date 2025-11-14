from __future__ import annotations

import logging

from quantum.infrastructure.observability.context.run_id import get_run_id
from quantum.infrastructure.observability.tracing.correlation.correlation_id import (
    get_correlation_id,
)

from ..base import PipelineStep


class CorrelationStep(PipelineStep):
    """Injects correlation_id and run_id."""

    def process(self, record: logging.LogRecord) -> bool:
        record.correlation_id = getattr(record, "correlation_id", get_correlation_id())
        record.run_id = getattr(record, "run_id", get_run_id())
        return True
