from __future__ import annotations

from quantum.infrastructure.observability.logging.pipeline.definitions import (
    StepDefinition,
)
from quantum.infrastructure.observability.logging.pipeline.steps.attrs_extract import (
    AttrsExtractStep,
)
from quantum.infrastructure.observability.logging.pipeline.steps.attrs_merge import (
    AttrsMergeStep,
)
from quantum.infrastructure.observability.logging.pipeline.steps.correlation import (
    CorrelationStep,
)
from quantum.infrastructure.observability.logging.pipeline.steps.exception_enrichment import (
    ExceptionEnrichmentStep,
)
from quantum.infrastructure.observability.logging.pipeline.steps.ignore_libraries import (
    IgnoreLibrariesStep,
)
from quantum.infrastructure.observability.logging.pipeline.steps.redaction import (
    RedactionStep,
)
from quantum.infrastructure.observability.logging.pipeline.steps.resource_metadata import (
    ResourceMetadataStep,
)
from quantum.infrastructure.observability.logging.pipeline.steps.timestamps import (
    TimestampStep,
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
        key="redaction",
        enabled_flag="enable_redaction",
        factory=lambda bundle=None: RedactionStep(),
    ),
]
