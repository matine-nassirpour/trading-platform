from __future__ import annotations

import logging

from collections.abc import Iterable
from typing import Final

from quantum.infrastructure.observability.logging.pipeline.engine.base import (
    PipelineStep,
)
from quantum.infrastructure.observability.logging.runtime.metrics import define_counter

_LOGGING_PIPELINE_STEP_FAILURES: Final = define_counter(
    "logging_pipeline_step_failures"
)


class LoggingPipeline(logging.Filter):
    """
    Deterministic and certifiable logging pipeline orchestrator.

    - Steps are executed sequentially.
    - A step can stop propagation by returning False.
    - Fully testable: each step is isolated.
    - Fault-resistant: pipeline never interrupts.
    """

    def __init__(self, steps: Iterable[PipelineStep]) -> None:
        super().__init__()
        self._steps: list[PipelineStep] = list(steps)

    def filter(self, record: logging.LogRecord) -> bool:
        for step in self._steps:
            try:
                if not step.process(record):
                    return False
            except Exception:
                # Never break the chain
                _LOGGING_PIPELINE_STEP_FAILURES.inc()
                logging.getLogger(__name__).exception(
                    "Logging pipeline step failed",
                    extra={"step": step.__class__.__name__},
                )
                return False
        return True
