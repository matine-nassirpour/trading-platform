"""
Infrastructure-level DTOs extracted from LogRecord.

These structures intentionally mirror the contract blocks but serve a
different architectural layer:
    - DTOs are transient, infra-facing, and reflect the technical shape
      of data coming from the logging subsystem.
    - They are free to evolve as the adapter changes.
    - They carry no schema guarantees and no versioning constraints.

This apparent duplication with the contract is deliberate: DTOs must remain
decoupled from the versioned domain contract to preserve strict layering,
testability, backward compatibility, and long-term schema stability.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True, slots=True)
class TimestampsDTO:
    """Infrastructure timestamps extracted from LogRecord."""

    timestamp_rfc3339: str
    ts_unix_ms: int
    ts_monotonic_ms: int


@dataclass(frozen=True, slots=True)
class SeverityDTO:
    """Normalized severity level (OTel-aligned)."""

    level_text: str
    severity_number: int


@dataclass(frozen=True, slots=True)
class MessageDTO:
    """Logger name + rendered message."""

    logger_name: str
    message: str


@dataclass(frozen=True, slots=True)
class ResourceDTO:
    """Execution environment metadata."""

    env: str | None
    instance_id: str
    service_name: str | None
    service_version: str | None
    service_namespace: str | None


@dataclass(frozen=True, slots=True)
class CorrelationDTO:
    """Tracing + correlation IDs (OTel + domain IDs)."""

    trace_id: str | None
    span_id: str | None
    sampled: bool | None
    correlation_id: str | None
    run_id: str | None


@dataclass(frozen=True, slots=True)
class ExceptionRawDTO:
    """Raw exception information extracted from LogRecord."""

    exc_type: str | None = None
    exc_message: str | None = None
    exc_stacktrace: str | None = None
    exc_summary: str | None = None


@dataclass(frozen=True, slots=True)
class InternalLogEvent:
    """
    Infrastructure DTO representing one log event after transformation
    from Python's LogRecord.

    This DTO is:
      - strictly compositional
      - minimal and responsibility-pure
      - decoupled from Pydantic, domain and schema logic
      - aligned with the structure of LogEventContractV1
      - designed for long-term compatibility
    """

    timestamps: TimestampsDTO
    severity: SeverityDTO
    message: MessageDTO
    resource: ResourceDTO
    correlation: CorrelationDTO
    exception: ExceptionRawDTO
    attrs: Mapping[str, Any] = field(default_factory=dict)
