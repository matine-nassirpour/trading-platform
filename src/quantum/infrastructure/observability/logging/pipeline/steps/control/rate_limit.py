from __future__ import annotations

import logging

from quantum.infrastructure.observability.logging.pipeline.engine.step import (
    PipelineStep,
)
from quantum.infrastructure.observability.logging.pipeline.state.rate_limit_state import (
    RateLimitState,
)


class RateLimitStep(PipelineStep):
    """
    Controls the rate of emitted log records using a token bucket algorithm.
    """

    __slots__ = "_state"

    def __init__(self, state: RateLimitState) -> None:
        self._state = state

    def process(self, record: logging.LogRecord) -> bool:
        return self._state.consume_token()
