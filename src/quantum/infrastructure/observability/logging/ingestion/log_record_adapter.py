from __future__ import annotations

import logging

from typing import Final

from quantum.infrastructure.observability.logging.foundation.constants.severity_map import (
    canonical_severity,
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
from quantum.infrastructure.observability.logging.runtime.exception_processor import (
    ExceptionProcessor,
)
from quantum.infrastructure.observability.logging.runtime.metrics import define_counter
from quantum.infrastructure.observability.logging.runtime.trace_context import (
    extract_trace_context,
)
from quantum.infrastructure.time.time_format import now_mono_ms, to_rfc3339_ms

_ADAPTER_RECOVERABLE_ERRORS: Final = define_counter(
    "logging_adapter_recoverable_errors"
)


class LogRecordAdapter:
    """
    Convert a Python LogRecord into a structured InternalLogEvent DTO.

    Responsibilities:
      - Safe extraction (NEVER raises)
      - Timestamp normalization (RFC3339, epoch ms, monotonic ms)
      - Severity mapping (canonical severity)
      - Trace context extraction (OpenTelemetry)
      - Raw exception extraction (no normalization)
      - Attribute sanitization (JSON safe)
      - Composition into infrastructure DTO blocks
    """

    @staticmethod
    def to_internal_event(
        record: logging.LogRecord,
        instance_id: str,
    ) -> InternalLogEvent:
        """
        Convert LogRecord → InternalLogEvent safely and deterministically.
        This function MUST NOT raise.
        """

        # ----------------------------------------------------------------------
        # Timestamps (LogRecord.created is seconds since epoch)
        # ----------------------------------------------------------------------
        created_ts = getattr(record, "created", 0.0)
        ts_unix_ms = int(created_ts * 1000) if created_ts else 0

        ts_mono_ms = now_mono_ms()
        timestamp = to_rfc3339_ms(created_ts)

        timestamps = TimestampsDTO(
            timestamp=timestamp,
            ts_unix_ms=ts_unix_ms,
            ts_monotonic_ms=ts_mono_ms,
        )

        # ----------------------------------------------------------------------
        # Severity
        # ----------------------------------------------------------------------
        levelno = getattr(record, "levelno", logging.INFO)
        level, sev_num = canonical_severity(int(levelno))

        severity = SeverityDTO(
            level=level,
            severity_number=sev_num,
        )

        # ----------------------------------------------------------------------
        # Message block
        # ----------------------------------------------------------------------
        try:
            message_text = record.getMessage()
        except Exception:
            _ADAPTER_RECOVERABLE_ERRORS.inc()
            message_text = "<unrenderable log message>"

        message = MessageDTO(
            logger=getattr(record, "name", "unknown_logger"),
            message=message_text,
        )

        # ----------------------------------------------------------------------
        # Resource block
        # ----------------------------------------------------------------------
        resource = ResourceDTO(
            env=getattr(record, "env", None),
            instance_id=instance_id,
            service_name=getattr(record, "service_name", None),
            service_version=getattr(record, "service_version", None),
            service_namespace=getattr(record, "service_namespace", None),
        )

        # ----------------------------------------------------------------------
        # Correlation block (OTel + domain correlation + run_id)
        # ----------------------------------------------------------------------
        trace_id, span_id, is_sampled = extract_trace_context()

        correlation = CorrelationDTO(
            trace_id=trace_id,
            span_id=span_id,
            sampled=is_sampled,
            correlation_id=getattr(record, "correlation_id", None),
            run_id=getattr(record, "run_id", None),
        )

        # ----------------------------------------------------------------------
        # Exception block (raw)
        # ----------------------------------------------------------------------
        exc_raw = ExceptionProcessor.extract(record)

        exception = ExceptionRawDTO(
            exception_summary=exc_raw.get("exception_summary"),
            exception_type=exc_raw.get("exception_type"),
            exception_message=exc_raw.get("exception_message"),
            exception_stacktrace=exc_raw.get("exception_stacktrace"),
        )

        # ----------------------------------------------------------------------
        # Final DTO orchestration
        # ----------------------------------------------------------------------
        attrs = getattr(record, "attrs", None)
        if not isinstance(attrs, dict):
            attrs = {}

        return InternalLogEvent(
            timestamps=timestamps,
            severity=severity,
            message=message,
            resource=resource,
            correlation=correlation,
            exception=exception,
            attrs=attrs,
        )
