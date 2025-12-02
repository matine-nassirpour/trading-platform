from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from quantum.infrastructure.observability.foundation.config.identity_runtime_bundle import (
    IdentityRuntimeBundle,
)
from quantum.infrastructure.observability.logging.pipeline.engine.pipeline_config import (
    PipelineConfig,
)


@dataclass(frozen=True, slots=True)
class LoggingRuntimeBundle:
    """
    Immutable Value Object consumed by the logging subsystem.

    Contains only validated, normalized, runtime-ready fields.
    No direct coupling to Settings or Pydantic types.
    """

    identity: IdentityRuntimeBundle

    # Directories
    log_dir: Path | None
    audit_dir: Path | None

    # Allowlist
    audit_allowlist: frozenset[str]

    # Logging main config
    log_level: int
    sample_info_every: int
    ratelimit_rps: float

    log_fsync: bool
    log_max_bytes: int
    log_warn_bytes: int

    # Handlers
    enable_partition_handler: bool
    enable_console_handler: bool = True

    pipeline_config: PipelineConfig = field(default_factory=PipelineConfig)
