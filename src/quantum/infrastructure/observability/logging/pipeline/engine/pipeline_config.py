from dataclasses import dataclass


@dataclass(frozen=True)
class PipelineConfig:
    enable_ignore_libraries: bool = True
    enable_unified_attrs: bool = True
    enable_exception_enrichment: bool = True
    enable_resource_metadata: bool = True
    enable_correlation: bool = True
    enable_info_sampler: bool = True
    enable_rate_limit: bool = True
    enable_redaction: bool = True
