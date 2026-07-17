"""
Versioned domain-level logging contract (V1).

These blocks intentionally resemble the internal DTOs but define a stable,
long-term interface that is:
    - immutable,
    - domain-facing,
    - schema-governed,
    - versioned and suitable for multi-year compatibility guarantees.

The duplication with the DTO layer is intentional: the contract must remain
independent of infrastructure concerns to support strict Clean Architecture,
controlled schema evolution (V1 → V2 → ...), and formal auditability.
"""

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any, Final


@dataclass(frozen=True, slots=True)
class TimestampsBlock:
    """Contractual timestamp block (domain-level)."""

    timestamp: str
    ts_unix_ms: int
    ts_monotonic_ms: int


@dataclass(frozen=True, slots=True)
class SeverityBlock:
    """Contractual severity block (OTel-aligned)."""

    level: str
    severity_number: int


@dataclass(frozen=True, slots=True)
class MessageBlock:
    """Contract for source logger + message."""

    logger: str
    message: str


@dataclass(frozen=True, slots=True)
class ResourceBlock:
    """Environment/resource identifiers."""

    env: str
    instance_id: str
    service_name: str | None
    service_version: str | None
    service_namespace: str | None


@dataclass(frozen=True, slots=True)
class CorrelationBlock:
    """Tracing + correlation identifiers."""

    trace_id: str | None
    span_id: str | None
    sampled: bool | None
    correlation_id: str | None
    run_id: str | None


@dataclass(frozen=True, slots=True)
class ExceptionBlockRaw:
    """Raw exception details before normalization."""

    exception_summary: str | None = None
    exception_type: str | None = None
    exception_message: str | None = None
    exception_stacktrace: str | None = None


@dataclass(frozen=True, slots=True)
class LogEventContractV1:
    """
    Immutable, domain-level contract representing one canonical logging event
    before Pydantic validation. This is the single formal schema bridging
    infrastructure DTOs and domain LogPayload models.

    This contract:
      - Is versioned (V1)
      - Does not depend on infrastructure (no LogRecord)
      - Does not depend on Pydantic
      - Provides a stable interface for all upstream/downstream components
      - Makes all mappings explicit and visible
      - Is suitable for long-term maintenance (10+ years)
    """

    timestamps: TimestampsBlock
    severity: SeverityBlock
    message: MessageBlock
    resource: ResourceBlock
    correlation: CorrelationBlock
    exception: ExceptionBlockRaw
    attrs: Mapping[str, Any] = field(default_factory=dict)
    version: Final[str] = "1.0.0"
