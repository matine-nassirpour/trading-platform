from __future__ import annotations

import logging
import time

from quantum.infrastructure.observability.logging.pipeline.engine.base import (
    PipelineStep,
)


class TimestampStep(PipelineStep):
    """Injects ts_monotonic_ms if absent."""

    def process(self, record: logging.LogRecord) -> bool:
        if not hasattr(record, "ts_monotonic_ms"):
            record.ts_monotonic_ms = time.monotonic_ns() // 1_000_000
        return True
