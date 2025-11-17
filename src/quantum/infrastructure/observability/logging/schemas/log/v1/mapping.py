from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from quantum.infrastructure.observability.logging.ingestion.internal_log_event import (
    CorrelationDTO,
    ExceptionRawDTO,
    InternalLogEvent,
    MessageDTO,
    ResourceDTO,
    SeverityDTO,
    TimestampsDTO,
)
from quantum.infrastructure.observability.logging.schemas.log.v1.contract import (
    CorrelationBlock,
    ExceptionBlockRaw,
    LogEventContractV1,
    MessageBlock,
    ResourceBlock,
    SeverityBlock,
    TimestampsBlock,
)
from quantum.infrastructure.observability.logging.schemas.log.v1.payload import (
    ExceptionBlock,
    LogPayloadV1,
)


# ╭────────────────────────────────────────────────────────────────────────────╮
# │ Mapper 1: InternalLogEvent → LogEventContractV1                            │
# ╰────────────────────────────────────────────────────────────────────────────╯
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
        timestamp_rfc3339=ts.timestamp_rfc3339,
        ts_unix_ms=ts.ts_unix_ms,
        ts_monotonic_ms=ts.ts_monotonic_ms,
    )

    # ─── severity
    sev: SeverityDTO = event.severity
    severity_block = SeverityBlock(
        level_text=sev.level_text,
        severity_number=sev.severity_number,
    )

    # ─── message
    msg: MessageDTO = event.message
    message_block = MessageBlock(
        logger_name=msg.logger_name,
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
        exc_type=exc.exc_type,
        exc_message=exc.exc_message,
        exc_stacktrace=exc.exc_stacktrace,
        exc_summary=exc.exc_summary,
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


# ╭────────────────────────────────────────────────────────────────────────────╮
# │ Mapper 2: Contract → LogPayloadV1 (pure domain model)                      │
# ╰────────────────────────────────────────────────────────────────────────────╯
def map_contract_to_payload(contract: LogEventContractV1) -> LogPayloadV1:
    """
    Convert a domain contract into a Pydantic-based LogPayloadV1.

    The Pydantic model ensures:
      - strict schema validation
      - invariants on timestamps, severity, correlation IDs, etc.
      - forensic-grade consistency
    """

    exc = contract.exception

    return LogPayloadV1(
        # ─── timestamps
        timestamp=contract.timestamps.timestamp_rfc3339,
        ts_unix_ms=contract.timestamps.ts_unix_ms,
        ts_monotonic_ms=contract.timestamps.ts_monotonic_ms,
        # ─── severity
        level=contract.severity.level_text,
        severity_number=contract.severity.severity_number,
        # ─── message
        logger=contract.message.logger_name,
        message=contract.message.message,
        # ─── resource
        env=contract.resource.env,
        instance=contract.resource.instance_id,
        service_name=contract.resource.service_name,
        service_version=contract.resource.service_version,
        service_namespace=contract.resource.service_namespace,
        # ─── correlation
        trace_id=contract.correlation.trace_id,
        span_id=contract.correlation.span_id,
        sampled=contract.correlation.sampled,
        correlation_id=contract.correlation.correlation_id,
        run_id=contract.correlation.run_id,
        # ─── exception
        exception_block=ExceptionBlock(
            exc_summary=exc.exc_summary,
            exception_type=exc.exc_type,
            exception_message=exc.exc_message,
            exception_stacktrace=exc.exc_stacktrace,
        ),
        # ─── schema metadata
        schema_name="quantum.log",
        log_schema_version="v1",
        # ─── flexible attributes
        attrs=contract.attrs,
    )
