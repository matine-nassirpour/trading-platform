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
    enable_console_handler: bool

    pipeline_config: PipelineConfig = field(default_factory=PipelineConfig)

    def __post_init__(self):
        if self.log_dir is not None and not self.log_dir.is_absolute():
            raise ValueError("LoggingRuntimeBundle.log_dir must be absolute or None.")

        if self.audit_dir is not None and not self.audit_dir.is_absolute():
            raise ValueError("LoggingRuntimeBundle.audit_dir must be absolute or None.")

        if self.sample_info_every < 0:
            raise ValueError("sample_info_every must be ≥ 0.")

        if self.ratelimit_rps < 0:
            raise ValueError("ratelimit_rps must be ≥ 0.")

        if self.log_max_bytes < 0:
            raise ValueError("log_max_bytes must be ≥ 0.")

        if self.log_warn_bytes < 0:
            raise ValueError("log_warn_bytes must be ≥ 0.")

        if not isinstance(self.audit_allowlist, frozenset):
            raise TypeError("audit_allowlist must be a frozenset[str].")
