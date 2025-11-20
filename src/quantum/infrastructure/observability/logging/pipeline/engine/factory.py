from __future__ import annotations

from quantum.infrastructure.observability.logging.metadata.config_bundle import (
    LoggingRuntimeBundle,
)
from quantum.infrastructure.observability.logging.pipeline.engine.pipeline import (
    LoggingPipeline,
)
from quantum.infrastructure.observability.logging.pipeline.engine.registry import (
    PIPELINE_STEP_REGISTRY,
)
from quantum.infrastructure.observability.logging.pipeline.steps.control.info_sampler import (
    InfoSamplerState,
)
from quantum.infrastructure.observability.logging.pipeline.steps.control.rate_limit import (
    RateLimitState,
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

        # instantiate shared/external state stores
        info_sampler_state = InfoSamplerState(sample_every=bundle.sample_info_every)
        rate_limit_state = RateLimitState(max_per_sec=bundle.ratelimit_rps)

        for step_def in PIPELINE_STEP_REGISTRY:
            if getattr(config, step_def.enabled_flag, False):
                if step_def.key == "info_sampler":
                    step = step_def.factory(info_sampler_state)
                elif step_def.key == "rate_limit":
                    step = step_def.factory(rate_limit_state)
                else:
                    step = step_def.factory(bundle)

                steps.append(step)

        return LoggingPipeline(steps)
