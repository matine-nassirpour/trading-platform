from __future__ import annotations

from quantum.infrastructure.observability.logging.pipeline.engine.definitions import (
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
from quantum.infrastructure.observability.logging.pipeline.steps.enrichment.attrs_extract import (
    AttrsExtractStep,
)
from quantum.infrastructure.observability.logging.pipeline.steps.enrichment.attrs_merge import (
    AttrsMergeStep,
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
from quantum.infrastructure.observability.logging.pipeline.steps.enrichment.timestamps import (
    TimestampStep,
)
from quantum.infrastructure.observability.logging.pipeline.steps.security.redaction import (
    RedactionStep,
)

PIPELINE_STEP_REGISTRY: list[StepDefinition] = [
    StepDefinition(
        key="ignore_libraries",
        enabled_flag="enable_ignore_libraries",
        factory=lambda bundle=None: IgnoreLibrariesStep(),
    ),
    StepDefinition(
        key="attrs_extract",
        enabled_flag="enable_attrs_extract",
        factory=lambda bundle=None: AttrsExtractStep(),
    ),
    StepDefinition(
        key="exception_enrichment",
        enabled_flag="enable_exception_enrichment",
        factory=lambda bundle=None: ExceptionEnrichmentStep(),
    ),
    StepDefinition(
        key="timestamps",
        enabled_flag="enable_timestamps",
        factory=lambda bundle=None: TimestampStep(),
    ),
    StepDefinition(
        key="attrs_merge",
        enabled_flag="enable_attrs_merge",
        factory=lambda bundle=None: AttrsMergeStep(),
    ),
    StepDefinition(
        key="resource_metadata",
        enabled_flag="enable_resource_metadata",
        factory=lambda bundle=None: ResourceMetadataStep(
            env=bundle.env,
            namespace=bundle.namespace,
            name=bundle.app_name,
            version=bundle.app_version,
        ),
    ),
    StepDefinition(
        key="correlation",
        enabled_flag="enable_correlation",
        factory=lambda bundle=None: CorrelationStep(),
    ),
    StepDefinition(
        key="info_sampler",
        enabled_flag="enable_info_sampler",
        factory=lambda bundle=None: InfoSamplerStep(
            sample_every=bundle.sample_info_every
        ),
    ),
    StepDefinition(
        key="rate_limit",
        enabled_flag="enable_rate_limit",
        factory=lambda bundle=None: RateLimitStep(max_per_sec=bundle.ratelimit_rps),
    ),
    StepDefinition(
        key="redaction",
        enabled_flag="enable_redaction",
        factory=lambda bundle=None: RedactionStep(),
    ),
]
