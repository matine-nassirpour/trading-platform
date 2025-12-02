from __future__ import annotations

from quantum.infrastructure.observability.logging.pipeline.engine.argument_kind import (
    StepArgumentKind,
)
from quantum.infrastructure.observability.logging.pipeline.engine.step_definition import (
    StepDefinition,
)
from quantum.infrastructure.observability.logging.pipeline.steps.control.ignore_libraries import (
    IgnoreLibrariesStep,
)
from quantum.infrastructure.observability.logging.pipeline.steps.control.info_sampler import (
    InfoSamplerStep,
)
from quantum.infrastructure.observability.logging.pipeline.steps.control.rate_limit import (
    RateLimitStep,
)
from quantum.infrastructure.observability.logging.pipeline.steps.enrichment.correlation import (
    CorrelationStep,
)
from quantum.infrastructure.observability.logging.pipeline.steps.enrichment.exception_enrichment import (
    ExceptionEnrichmentStep,
)
from quantum.infrastructure.observability.logging.pipeline.steps.enrichment.resource_metadata import (
    ResourceMetadataStep,
)
from quantum.infrastructure.observability.logging.pipeline.steps.enrichment.unified_attrs import (
    UnifiedAttrsStep,
)
from quantum.infrastructure.observability.logging.pipeline.steps.security.redaction import (
    RedactionStep,
)

# ╭────────────────────────────────────────────────────────────────────────────╮
# │                  PIPELINE ORDER — INDUSTRY-GRADE                           │
# │ -------------------------------------------------------------------------- │
# │ 1. ignore_libraries        → remove the noise                              │
# │ 2. exception_enrichment    → Extract & Normalize RAW Exceptions            │
# │ 3. unified_attrs           → merge + normalization + JSON sanitization     │
# │ 4. resource_metadata       → stable & deterministic enrichment             │
# │ 5. correlation             → correlation_id / run_id                       │
# │ 6. info_sampler            → sampling application-level                    │
# │ 7. rate_limit              → rate limiting                                 │
# │ 8. redaction               → security (secrets, JWT, entropy)              │
# │                                                                            │
# │ The above order is the optimal production-grade standard,                  │
# │ and eliminates all inconsistency problems in record.attrs.                 │
# ╰────────────────────────────────────────────────────────────────────────────╯

PIPELINE_STEP_REGISTRY: list[StepDefinition] = [
    StepDefinition(
        key="ignore_libraries",
        enabled_flag="enable_ignore_libraries",
        factory=lambda _arg=None: IgnoreLibrariesStep(),
        arg_kind=StepArgumentKind.NONE,
    ),
    StepDefinition(
        key="exception_enrichment",
        enabled_flag="enable_exception_enrichment",
        factory=lambda _arg=None: ExceptionEnrichmentStep(),
        arg_kind=StepArgumentKind.NONE,
    ),
    StepDefinition(
        key="unified_attrs",
        enabled_flag="enable_unified_attrs",
        factory=lambda _arg=None: UnifiedAttrsStep(),
        arg_kind=StepArgumentKind.NONE,
    ),
    StepDefinition(
        key="resource_metadata",
        enabled_flag="enable_resource_metadata",
        factory=lambda bundle: ResourceMetadataStep(identity=bundle.identity),
        arg_kind=StepArgumentKind.BUNDLE,
    ),
    StepDefinition(
        key="correlation",
        enabled_flag="enable_correlation",
        factory=lambda _arg=None: CorrelationStep(),
        arg_kind=StepArgumentKind.NONE,
    ),
    StepDefinition(
        key="info_sampler",
        enabled_flag="enable_info_sampler",
        factory=lambda state: InfoSamplerStep(state),
        arg_kind=StepArgumentKind.INFO_SAMPLER_STATE,
    ),
    StepDefinition(
        key="rate_limit",
        enabled_flag="enable_rate_limit",
        factory=lambda state: RateLimitStep(state),
        arg_kind=StepArgumentKind.RATE_LIMIT_STATE,
    ),
    StepDefinition(
        key="redaction",
        enabled_flag="enable_redaction",
        factory=lambda _arg=None: RedactionStep(),
        arg_kind=StepArgumentKind.NONE,
    ),
]
