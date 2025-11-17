from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class LoggingRuntimeBundle:
    env: str
    namespace: str
    app_name: str
    app_version: str
    instance_id: str

    audit_allowlist: set[str]

    log_dir: str | None
    audit_dir: str | None

    log_level: int
    sample_info_every: int
    ratelimit_rps: float

    log_fsync: bool
    log_max_bytes: int
    log_warn_bytes: int

    enable_partition_handler: bool
    enable_console_handler: bool = True
