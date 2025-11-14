from __future__ import annotations

from dataclasses import dataclass

from quantum.infrastructure.observability.logging.config_bundle import (
    LoggingRuntimeBundle,
)

from .pipeline import LoggingPipeline
from .steps.attrs_merge import AttrsMergeStep
from .steps.correlation import CorrelationStep
from .steps.ignore_libraries import IgnoreLibrariesStep
from .steps.redaction import RedactionStep
from .steps.resource_metadata import ResourceMetadataStep
from .steps.timestamps import TimestampStep


# ╭────────────────────────────────────────────────────────────────────────────╮
# │ Pipeline configuration contract                                            │
# ╰────────────────────────────────────────────────────────────────────────────╯
@dataclass(frozen=True)
class PipelineConfig:
    """
    Immutable, industry-grade configuration for the logging pipeline.
    Designed for certifiable environments & versioned composition.

    Each field corresponds to a pipeline component that can be toggled,
    reordered, or overridden entirely.
    """

    enable_ignore_libraries: bool = True
    enable_timestamps: bool = True
    enable_attrs_merge: bool = True
    enable_resource_metadata: bool = True
    enable_correlation: bool = True
    enable_redaction: bool = True


# ╭────────────────────────────────────────────────────────────────────────────╮
# │ Pipeline Factory                                                           │
# ╰────────────────────────────────────────────────────────────────────────────╯
class LoggingPipelineFactory:
    """
    Factory responsible for constructing the logging pipeline based on
    a declarative configuration (PipelineConfig) and runtime bundle.

    Clean, testable, versionable, architecture-aligned.
    """

    @staticmethod
    def build(config: PipelineConfig, bundle: LoggingRuntimeBundle) -> LoggingPipeline:
        steps = []

        if config.enable_ignore_libraries:
            steps.append(IgnoreLibrariesStep())
        if config.enable_timestamps:
            steps.append(TimestampStep())
        if config.enable_attrs_merge:
            steps.append(AttrsMergeStep())
        if config.enable_resource_metadata:
            steps.append(
                ResourceMetadataStep(
                    env=bundle.env,
                    namespace=bundle.namespace,
                    name=bundle.app_name,
                    version=bundle.app_version,
                )
            )
        if config.enable_correlation:
            steps.append(CorrelationStep())
        if config.enable_redaction:
            steps.append(RedactionStep())

        return LoggingPipeline(steps)
