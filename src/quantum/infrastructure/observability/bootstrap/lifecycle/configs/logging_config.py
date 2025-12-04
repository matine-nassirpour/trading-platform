from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from quantum.infrastructure.observability.foundation.config.identity_runtime_bundle import (
    IdentityRuntimeBundle,
)


@dataclass(frozen=True)
class LoggingConfig:
    """
    Immutable value object describing all runtime configuration required
    for initializing the logging pipeline.

    This object is *independent* from configuration loading concerns and is
    the only information allowed to flow into LoggingInitializer.

    This ensures:
      • No dependency on ConfigManager
      • Strong separation of concerns
      • Full testability and predictability
      • Certification-ready design (DO-178C / IEC 62304 / ISO 26262)
    """

    identity: IdentityRuntimeBundle

    log_dir: Path
    audit_dir: Path

    audit_allowlist: frozenset[str]

    log_level: int
    sample_info_every: int
    ratelimit_rps: float

    log_fsync: bool
    log_max_bytes: int
    log_warn_bytes: int
