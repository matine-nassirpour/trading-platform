from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PipelineConfig:
    enable_ignore_libraries: bool = True
    enable_attrs_extract: bool = True
    enable_exception_enrichment: bool = True
    enable_timestamps: bool = True
    enable_attrs_merge: bool = True
    enable_resource_metadata: bool = True
    enable_correlation: bool = True
    enable_info_sampler: bool = True
    enable_rate_limit: bool = True
    enable_redaction: bool = True
