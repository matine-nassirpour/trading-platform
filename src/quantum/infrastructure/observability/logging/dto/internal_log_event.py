from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True, slots=True)
class InternalLogEvent:
    # ─── timestamps
    timestamp_rfc3339: str
    ts_unix_ms: int
    ts_monotonic_ms: int

    # ─── severity (OTel-compatible text)
    level_text: str
    severity_number: int

    # ─── logger metadata
    logger_name: str
    message: str

    # ─── environment / resource metadata
    env: str | None
    instance_id: str
    service_name: str | None
    service_version: str | None
    service_namespace: str | None

    # ─── tracing / correlation
    trace_id: str | None
    span_id: str | None
    sampled: bool | None
    correlation_id: str | None
    run_id: str | None

    # ─── exception block (raw, unnormalized)
    exception_type: str | None = None
    exception_message: str | None = None
    exception_stacktrace: str | None = None
    exception_summary: str | None = None

    # ─── flexible attributes
    attrs: Mapping[str, Any] = field(default_factory=dict)
