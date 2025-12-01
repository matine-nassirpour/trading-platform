from __future__ import annotations

import logging

from quantum.infrastructure.observability.logging.pipeline.engine.step import (
    PipelineStep,
)
from quantum.infrastructure.observability.logging.pipeline.state.info_sampler_state import (
    InfoSamplerState,
)


class InfoSamplerStep(PipelineStep):
    """Samples INFO-level log records at a fixed interval."""

    __slots__ = ("_state",)

    def __init__(self, state: InfoSamplerState) -> None:
        self._state = state

    def process(self, record: logging.LogRecord) -> bool:
        if record.levelno != logging.INFO:
            return True
        return self._state.increment_and_check()
