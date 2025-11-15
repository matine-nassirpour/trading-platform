from __future__ import annotations

from quantum.infrastructure.observability.logging.config_bundle import (
    LoggingRuntimeBundle,
)
from quantum.infrastructure.observability.logging.pipeline.pipeline import (
    LoggingPipeline,
)
from quantum.infrastructure.observability.logging.pipeline.registry import (
    PIPELINE_STEP_REGISTRY,
)


class LoggingPipelineFactory:
    """
    Ultimate industry-grade pipeline factory:
    - no direct knowledge of steps
    - declarative composition
    - stable, predictable, certifiable
    - complexity ≈ 1
    """

    @staticmethod
    def build(config, bundle: LoggingRuntimeBundle) -> LoggingPipeline:
        steps = []

        for step_def in PIPELINE_STEP_REGISTRY:
            if getattr(config, step_def.enabled_flag, False):
                step = step_def.factory(bundle)
                steps.append(step)

        return LoggingPipeline(steps)
