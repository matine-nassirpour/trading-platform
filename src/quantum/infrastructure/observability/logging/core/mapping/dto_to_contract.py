from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from quantum.infrastructure.observability.logging.core.contracts.log_contract_v1 import (
    CorrelationBlock,
    ExceptionBlockRaw,
    LogEventContractV1,
    MessageBlock,
    ResourceBlock,
    SeverityBlock,
    TimestampsBlock,
)
from quantum.infrastructure.observability.logging.ingestion.internal_log_event import (
    CorrelationDTO,
    ExceptionRawDTO,
    InternalLogEvent,
    MessageDTO,
    ResourceDTO,
    SeverityDTO,
    TimestampsDTO,
)


def map_dto_to_contract(event: InternalLogEvent) -> LogEventContractV1:
    """
    Convert a structured InternalLogEvent (infrastructure DTO)
    into a strict domain-level contract (V1).

    Pure transformation:
      - no validation, no logging, no fallback
      - zero mutation
      - deterministic
      - stable contract interface
    """

    # ─── timestamps
    ts: TimestampsDTO = event.timestamps
    timestamps_block = TimestampsBlock(
        timestamp=ts.timestamp,
        ts_unix_ms=ts.ts_unix_ms,
        ts_monotonic_ms=ts.ts_monotonic_ms,
    )

    # ─── severity
    sev: SeverityDTO = event.severity
    severity_block = SeverityBlock(
        level=sev.level,
        severity_number=sev.severity_number,
    )

    # ─── message
    msg: MessageDTO = event.message
    message_block = MessageBlock(
        logger=msg.logger,
        message=msg.message,
    )

    # ─── resource
    res: ResourceDTO = event.resource
    resource_block = ResourceBlock(
        env=res.env,
        instance_id=res.instance_id,
        service_name=res.service_name,
        service_version=res.service_version,
        service_namespace=res.service_namespace,
    )

    # ─── correlation
    corr: CorrelationDTO = event.correlation
    correlation_block = CorrelationBlock(
        trace_id=corr.trace_id,
        span_id=corr.span_id,
        sampled=corr.sampled,
        correlation_id=corr.correlation_id,
        run_id=corr.run_id,
    )

    # ─── exception
    exc: ExceptionRawDTO = event.exception
    exception_block = ExceptionBlockRaw(
        exception_summary=exc.exception_summary,
        exception_type=exc.exception_type,
        exception_message=exc.exception_message,
        exception_stacktrace=exc.exception_stacktrace,
    )

    # ─── attributes
    attrs: Mapping[str, Any] = event.attrs

    # ─── final contract
    return LogEventContractV1(
        timestamps=timestamps_block,
        severity=severity_block,
        message=message_block,
        resource=resource_block,
        correlation=correlation_block,
        exception=exception_block,
        attrs=dict(attrs),  # create defensive copy
    )
