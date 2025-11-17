from __future__ import annotations

import logging
import threading

from quantum.infrastructure.observability.logging.pipeline.engine.base import (
    PipelineStep,
)


class InfoSamplerStep(PipelineStep):
    """Samples INFO-level log records at a fixed interval."""

    __slots__ = ("_sample_every", "_counter", "_lock")

    def __init__(self, sample_every: int = 10) -> None:
        self._sample_every = max(1, int(sample_every))
        self._counter = 0
        self._lock = threading.Lock()

    def process(self, record: logging.LogRecord) -> bool:
        if record.levelno != logging.INFO or self._sample_every <= 1:
            return True

        with self._lock:
            self._counter = (self._counter + 1) % self._sample_every
            return self._counter == 0
