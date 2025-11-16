from __future__ import annotations

from quantum.infrastructure.observability.logging.dto.internal_log_event import (
    InternalLogEvent,
)
from quantum.infrastructure.observability.logging.models.log_payload_v1 import (
    ExceptionBlock,
    LogPayloadV1,
)


class LogPayloadFactory:
    """
    Pure domain factory responsible for constructing a validated LogPayloadV1
    from an InternalLogEvent DTO.

    This class:
      - Has NO dependency on LogRecord or infrastructure
      - Has NO responsibility for timestamp generation, tracing extraction,
        sanitation, or override logic (handled upstream)
      - Produces deterministic and schema-compliant payloads
      - Enforces invariants required by LogPayloadV1
      - Can be unit-tested in complete isolation
    """

    @staticmethod
    def from_internal_event(event: InternalLogEvent) -> LogPayloadV1:
        """
        Bind the InternalLogEvent into a fully validated LogPayloadV1 model.
        No mutation, no side effects.
        """

        exception_block = ExceptionBlock(
            exception=event.exception_summary,
            exception_type=event.exception_type,
            exception_message=event.exception_message,
            exception_stacktrace=event.exception_stacktrace,
        )

        return LogPayloadV1(
            # timestamps
            timestamp=event.timestamp_rfc3339,
            ts_unix_ms=event.ts_unix_ms,
            ts_monotonic_ms=event.ts_monotonic_ms,
            # severity
            level=event.level_text,
            severity_number=event.severity_number,
            # logger
            logger=event.logger_name,
            message=event.message,
            # environment/resource
            env=event.env,
            instance=event.instance_id,
            service_name=event.service_name,
            service_version=event.service_version,
            service_namespace=event.service_namespace,
            # correlation / tracing
            trace_id=event.trace_id,
            span_id=event.span_id,
            sampled=event.sampled,
            correlation_id=event.correlation_id,
            run_id=event.run_id,
            # exceptions
            exception_block=exception_block,
            # schema metadata
            schema_name="quantum.log",
            log_schema_version="v1",
            # flexible attributes
            attrs=event.attrs,
        )
