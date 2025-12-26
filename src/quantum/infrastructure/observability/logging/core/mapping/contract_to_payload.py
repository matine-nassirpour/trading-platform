from __future__ import annotations

from quantum.infrastructure.observability.logging.core.contracts.log_contract_v1 import (
    LogEventContractV1,
)
from quantum.infrastructure.observability.logging.core.models.log_payload import (
    ExceptionBlock,
    LogPayload,
)
from quantum.infrastructure.observability.logging.foundation.constants.severity_map import (
    severity_text,
)


def map_contract_to_payload(contract: LogEventContractV1) -> LogPayload:
    """
    Convert a domain contract into a Pydantic-based LogPayload.

    The Pydantic model ensures:
      - strict schema validation
      - invariants on timestamps, severity, correlation IDs, etc.
      - forensic-grade consistency
    """

    level = severity_text(contract.severity.level)
    exc = contract.exception

    return LogPayload(
        # ─── timestamps
        timestamp=contract.timestamps.timestamp,
        ts_unix_ms=contract.timestamps.ts_unix_ms,
        ts_monotonic_ms=contract.timestamps.ts_monotonic_ms,
        # ─── severity
        level=level,
        severity_number=contract.severity.severity_number,
        # ─── message
        logger=contract.message.logger,
        message=contract.message.message,
        # ─── resource
        env=contract.resource.env,
        instance_id=contract.resource.instance_id,
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
            exception_summary=exc.exception_summary,
            exception_type=exc.exception_type,
            exception_message=exc.exception_message,
            exception_stacktrace=exc.exception_stacktrace,
        ),
        # ─── schema metadata
        schema_name="quantum.log",
        log_schema_version="v1",
        # ─── flexible attributes
        attrs=contract.attrs,
    )
