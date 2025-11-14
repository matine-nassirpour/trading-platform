from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


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

    level: int
    log_directory: Path | None
    audit_directory: Path | None

    rate_limit_per_sec: int
    sample_info_every: int

    deep_probe: bool

    service_name: str
    service_namespace: str
    service_version: str
    environment: str
    instance_id: str
