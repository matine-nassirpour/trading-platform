from typing import Any

from quantum.infrastructure.observability.foundation.config.logging_runtime_bundle import (
    LoggingRuntimeBundle,
)
from quantum.infrastructure.observability.logging.pipeline.engine.argument_kind import (
    StepArgumentKind,
)
from quantum.infrastructure.observability.logging.pipeline.engine.pipeline import (
    LoggingPipeline,
)
from quantum.infrastructure.observability.logging.pipeline.engine.pipeline_config import (
    PipelineConfig,
)
from quantum.infrastructure.observability.logging.pipeline.engine.registry import (
    PIPELINE_STEP_REGISTRY,
)
from quantum.infrastructure.observability.logging.pipeline.state.info_sampler_state import (
    InfoSamplerState,
)
from quantum.infrastructure.observability.logging.pipeline.state.rate_limit_state import (
    RateLimitState,
)


class LoggingPipelineFactory:
    """
    Ultimate certifiable factory:
    - no if/else special cases
    - fully declarative via StepArgumentKind
    - stable, predictable
    - compliant with high-integrity Clean Architecture
    """

    @staticmethod
    def build(config: PipelineConfig, bundle: LoggingRuntimeBundle) -> LoggingPipeline:
        # Pre-instantiated shared state resources
        info_sampler_state = InfoSamplerState(sample_every=bundle.sample_info_every)
        rate_limit_state = RateLimitState(max_per_sec=bundle.ratelimit_rps)

        steps = []
        arg: Any | None

        for step_def in PIPELINE_STEP_REGISTRY:
            # step enabled?
            if not getattr(config, step_def.enabled_flag, False):
                continue

            # Resolve constructor argument
            if step_def.arg_kind is StepArgumentKind.NONE:
                arg = None
            elif step_def.arg_kind is StepArgumentKind.BUNDLE:
                arg = bundle
            elif step_def.arg_kind is StepArgumentKind.INFO_SAMPLER_STATE:
                arg = info_sampler_state
            elif step_def.arg_kind is StepArgumentKind.RATE_LIMIT_STATE:
                arg = rate_limit_state
            else:
                raise ValueError(f"Unsupported StepArgumentKind: {step_def.arg_kind}")

            # Construct step
            step = step_def.factory(arg)
            steps.append(step)

        return LoggingPipeline(steps)
